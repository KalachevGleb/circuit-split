#include <iostream>
#include <vector>
#include <algorithm>
#include <stdexcept>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <any>
#include <random>

#include "timer.h"
#include "json.h"

using namespace std;

class Barrier {
public:
    explicit Barrier(std::size_t num_threads) : total_threads(num_threads), count(num_threads), generation(0) {}

    void synchronize() {
        std::unique_lock<std::mutex> lock(mutex);
        int current_generation = generation.load();

        if (--count == 0) {
            // Last thread to arrive at the barrier
            count = total_threads;
            generation++;
            // Notify all waiting threads
            cv.notify_all();
        } else {
            // Other threads wait
            cv.wait(lock, [this, current_generation] { return current_generation != generation.load(); });
        }
    }

private:
    std::mutex mutex;
    std::condition_variable cv;
    std::size_t total_threads;
    std::size_t count;
    atomic_int generation;
};

template<class T>
class Notifier {
public:
    void notify(T v, int nthreads) {
        std::unique_lock<std::mutex> lock(mutex);
        if (count.load() < nthreads) {
            cv2.wait(lock, [this, nthreads] { return count.load() == nthreads; });
        }
        data = v;
        generation++;
        count = 0;
        cv.notify_all();
    }
    T wait(int i) {
        std::unique_lock<std::mutex> lock(mutex);
        int step = generation.load();
        count++;
        cv2.notify_one();
        cv.wait(lock, [this, step] { return step < generation.load(); });
        return data;
    }

private:
    std::mutex mutex;
    std::condition_variable cv, cv2;
    atomic_int generation{0}, count{0};
    T data{};
};

class SpinLockBarrier {
private:
    std::atomic<int> count;
    std::atomic<int> generation;
    int total_threads = 0;
public:
    explicit SpinLockBarrier(int num_threads) : total_threads(num_threads), count(0), generation(0) {}

    void synchronize() {
        //constexpr size_t max_spins = 1600;
        int my_generation = generation.load();
        if (count.fetch_add(1) == total_threads - 1) {
            count.store(0);
            generation++;
        } else {
            size_t iter = 0;
            while (generation.load() == my_generation) {
                this_thread::yield();
                // spin
            }
        }
    }
};

struct CircuitGraph {
    size_t num_nodes = 0;
    vector<int> node_weights;   // weight of each node
    vector<int> node_depth;     // depth of each node (max distance from input)
    vector<vector<int>> deps;   // dependencies of each node
    vector<vector<int>> reg_deps; // nodes that depend on each node
    vector<vector<int>> layers; // layers of nodes (nodes in the same layer can be computed in parallel)
    vector<uint32_t> node_data; // raw array of node data
    vector<int> data_pos;       // position of each node's data in node_data
    vector<int> dep_data_ptr;   // pointer to the dependency data of each node in node_data
    vector<int> dep_data_pos;   // position of each node's dependency pointer in dep_data_ptr
    vector<int> dep_weights;    // total weight of each node's dependencies
    vector<pair<int, int>> reg_edges; // edges corresponding to register switches

    enum NotifyType { PAUSE, RESUME, STOP };
    vector<vector<vector<int>>> thread_layers; // layers of nodes for each thread
    unique_ptr<Notifier<NotifyType>> notifier; // notifier for pausing and resuming threads
    unique_ptr<SpinLockBarrier> spin_barrier;  // spin lock barrier for thread synchronization
    unique_ptr<Barrier> barrier;              // barrier for thread synchronization (one of the two barriers is used)
    vector<thread> threads;                  // threads for parallel execution


    explicit CircuitGraph(const JSON& json) {
        json.at("node_weights").get(node_weights);
        num_nodes = node_weights.size();
        auto edges = json.at("edges").as<vector<pair<int, int>>>();
        if (json.contains("reg_edges")) {
            json.at("reg_edges").get(reg_edges);
        }
        for(int&w : node_weights) {
            w = max(w, 1);
        }
        deps.resize(num_nodes);
        for (auto [to, from] : edges) {
            deps[to].push_back(from);
            //backward[from].push_back(to);
        }
        node_depth.resize(num_nodes, -1);
        for (int i = 0; i < num_nodes; i++) {
            if (deps[i].empty()) {
                node_depth[i] = 0;
            }
        }

        int total_weight = 0, total_dep_weight = 0;
        for (int i = 0; i < num_nodes; i++) {
            int d = _updateDepthRecursive(i);
            if (d>=layers.size()) {
                layers.resize(d+1);
            }
            layers[d].push_back(i);
            total_weight += node_weights[i];
            for (int dep : deps[i]) {
                total_dep_weight += node_weights[dep];
            }
        }
        // allocate node_data and dep_data_ptr
        node_data.assign(total_weight, 0x12345678);
        data_pos.resize(num_nodes);
        dep_data_ptr.resize(total_dep_weight);
        dep_data_pos.resize(num_nodes);
        dep_weights.resize(num_nodes);
        int pos = 0, dep_pos = 0;
        for (auto & layer : layers) {
            for (int node : layer) {
                data_pos[node] = pos;
                pos += node_weights[node];
                dep_data_pos[node] = dep_pos;
                for (int dep : deps[node]) {
                    int dep_weight = node_weights[dep];
                    int dep_start = data_pos[dep];
                    for (int i = 0; i < dep_weight; i++) {
                        dep_data_ptr[dep_pos++] = dep_start + i;
                    }
                }
                dep_weights[node] = dep_pos - dep_data_pos[node];
            }
        }
    }

    void start_threads(int num_threads) {
        if (!threads.empty()) {
            throw runtime_error("threads already started");
        }
        barrier = make_unique<Barrier>(num_threads+1); // +1 for the main thread
        notifier = make_unique<Notifier<NotifyType>>(); // sync worker threads
        spin_barrier = make_unique<SpinLockBarrier>(num_threads); // sync worker threads
        threads.resize(num_threads);
        for (int i = 0; i < num_threads; i++) {
            threads[i] = thread([this, i] { run_thread(i); });
        }
    }

    void stop_threads() {
        if(threads.empty()) return; // already stopped
        notifier->notify(NotifyType::STOP, threads.size());
        for (auto& t: threads) {
            if (t.joinable()) {
                t.join();
            }
        }
        threads.clear();
    }

    void switch_regs(size_t b, size_t e) {
        // switch registers in range from b to e
        for (size_t i = b; i < e; i++) {
            auto [to, from] = reg_edges[i];
            int from_pos = data_pos[from], to_pos = data_pos[to];
            int w = node_weights[from];
            for (int j = 0; j < w; j++) {
                node_data[to_pos+j] = node_data[from_pos+j];
            }
        }
    }
    void process_node(int node) { // моделирование вычисления значения узла (моделируется чтение данных, вычисление и запись)
        // сумма всех компонентов аргументов запивывается во все компоненты результата (все компоненты результата одинаковы)
        int pos = data_pos[node], w = node_weights[node];
        int dep_pos = dep_data_pos[node];
        int dep_weight = dep_weights[node];
        uint32_t sum = 0;
        for (int i = 0; i < dep_weight; i++) {
            sum += node_data[dep_data_ptr[dep_pos++]];
        }
        for (int i = 0; i < w; i++) {
            node_data[pos + i] = sum;
        }
    }

    void run_thread(int thread_id) {
        auto &curr_layers = thread_layers[thread_id];
        int cycle = 0;
        while (true) {
            auto nr = notifier->wait(thread_id);  // wait for notification from main thread
            if (nr == STOP) {
                break;
            } else if (nr == PAUSE) {
                continue;
            }
            cycle++;
            //cout << "start cycle " << cycle << endl;
            // register switch
            switch_regs(reg_edges.size() * thread_id / threads.size(), reg_edges.size() * (thread_id+1) / threads.size());
            // compute nodes
            for (int il = 0; il < layers.size(); il++) {
                // wait for other worker threads to finish previous layer
                spin_barrier->synchronize();
                //barrier->synchronize();
                for (int node: curr_layers[il]) {
                    process_node(node);
                }
            }
        }
    }
    void split_for_threads(int num_threads) {
        auto nlayers = layers.size();
        thread_layers.assign(num_threads, vector<vector<int>>(nlayers));
        for (int i = 0; i < nlayers; i++) {
            int weight = 0;
            for (int node: layers[i]) {
                weight += dep_weights[node];
            }
            int curr_weight = 0, curr_thread = 0;
            for (int node: layers[i]) {
                if (curr_weight*num_threads > weight*(curr_thread+1)) {
                    curr_thread++;
                }
                curr_weight += dep_weights[node];
                thread_layers[curr_thread][i].push_back(node);
            }
        }
        start_threads(num_threads);
    }

    void print_layers() {
        for (int i = 0; i < layers.size(); i++) {
            cout << "Layer " << i << ": ";
            for (int node: layers[i]) {
                cout << node << " ";
            }
            cout << endl;
        }
    }

    void compute() {
        switch_regs(0, reg_edges.size());
        for (auto &layer: layers) {
            for (int node: layer) {
                process_node(node);
            }
        }
    }
    void compute_parallel(int steps = 1) {
        if(threads.empty()) {
            throw runtime_error("threads not started");
        }
        for (int i=0; i<steps; i++) {
            notifier->notify(NotifyType::RESUME, threads.size());
        }
        notifier->notify(NotifyType::PAUSE, threads.size());
    }

private:
    int _updateDepthRecursive(int node) {
        int res = node_depth[node];
        if (res >= 0) {
            return res;
        } else if (res == -2) {
            throw invalid_argument("CircuitGraph has a cycle");
        }
        node_depth[node] = -2;
        res = 0;
        for (int dep : deps[node]) {
            res = max(res, _updateDepthRecursive(dep) + 1);
        }
        return node_depth[node] = res;
    }
};



int main(int argc, char *argv[]) {
    // argv[1] is the input file
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <input.json>" << endl;
        return 1;
    }
    Timer timer;
    auto input = JSON::load(argv[1]);
    cout << "Load time: " << timer.getTime() << " s" << endl;
    timer.reset();
    CircuitGraph graph(input);
    cout << "Graph initialization time: " << timer.getTime() << " s" << endl;

    cout << "Number of nodes: " << graph.num_nodes << endl;
    cout << "Number of layers: " << graph.layers.size() << endl;
    //graph.print_layers();

    constexpr double timeout = 1.0;
    timer.reset();
    int count = 0;
    do {
        graph.compute();
        count++;
    } while (timer.getTime() < timeout);
    double time_per_cycle = timer.getTime() / count;
    cout << "Average time per cycle: " << time_per_cycle << " s" << endl;

    for (int num_threads = 1; num_threads <= 16; num_threads++) {
        graph.split_for_threads(num_threads);
        timer.reset();
        count = 0;
        do {
            count+=100;
            graph.compute_parallel(100);
        } while (timer.getTime() < timeout);
        double time_per_cycle_par = timer.getTime() / count;
        cout << "Average time per cycle with " << num_threads << ": ";
        cout << time_per_cycle_par << " s (" << time_per_cycle / time_per_cycle_par << "x speedup)" << endl;
        graph.stop_threads();
    }

    return 0;
}
