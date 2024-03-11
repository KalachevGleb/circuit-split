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
#include <fstream>
#include <sstream>
#include <filesystem>

#include "timer.h"
#include "json.h"
#include "argparse.h"
#include "utils.h"
#include "checksum.h"

using namespace std;

// null output name
#ifdef _WIN32
#define NULL_OUTPUT "NUL"
#else
#define NULL_OUTPUT "/dev/null"
#endif

template<class Cont, class T>
bool contains(const Cont &c, const T &v) {
    return find(c.begin(), c.end(), v) != c.end();
}

struct CircuitGraph {
    size_t num_nodes = 0;
    vector<int> node_weights;   // weight of each node
    vector<int> node_depth;     // depth of each node (max distance from input)
    vector<vector<int>> deps;   // dependencies of each node
    vector<vector<int>> reg_deps; // nodes that depend on each node
    vector<pair<int, int>> reg_edges; // edges corresponding to register switches
    vector<int> mem_order;      // order nodes in memory
    vector<vector<pair<int, int>>> schedule; /* schedule for each thread;
                                              * it is a list of pairs (type, j) where type in {0,1} and:
                                              *   if type == 0: j is the index of the node to be calculated
                                              *   if type == 1: j is the synchronization point (barrier)
                                              * */
    vector<pair<vector<int>, vector<int>>> sync_points; // synchronization points;
    // for pair (X, Y) all threads from Y must reach the barrier before any thread from X can proceed
    // That is, all threads from X will wait at the barrier until all threads from Y reach it
    int nthreads = 0;

    //--------------------------------------------------------------------------------

    explicit CircuitGraph(const JSON& json) {
        const JSON& cg = json.at("graph");
        cg.at("node_weights").get(node_weights);
        num_nodes = node_weights.size();
        auto edges = cg.at("edges").as<vector<pair<int, int>>>();
        if (cg.contains("reg_edges")) {
            cg.at("reg_edges").get(reg_edges);
        }

        for (int&w : node_weights) {
            w = max(w, 1);
        }
        deps.resize(num_nodes);
        for (auto [to, from] : edges) {
            deps[to].push_back(from);
            //backward[from].push_back(to);
        }
        json.at("memory_order").get(mem_order);
        json.at("schedule").get(schedule);
        json.at("sync_points").get(sync_points);
        nthreads = int(schedule.size());
    }

    bool checkCorrectness() const {
        int nerr = 0;
        // 1. Check that all non-input nodes are present in the schedule
        vector<int> not_present_mo, not_present_sch, duplicated_mo, duplicated_sch, invalid_mo, invalid_sch, duplicated_syncp;
        vector<int> count_mo(num_nodes, 0), count_sch(num_nodes, 0);
        // 1a. Check memory order
        for (int i : mem_order) {
            if(i >= num_nodes || i < 0) {
                invalid_mo.push_back(i);
            } else {
                count_mo[i]++;
            }
        }
        for (size_t i = 0; i < count_mo.size(); i++) {
            if (count_mo[i] > 1) {
                duplicated_mo.push_back(i);
            } else if (count_mo[i] == 0) {
                not_present_mo.push_back(i);
            }
        }
        auto report_err = [&nerr](vector<int>& v, const string& msg) {
            if (v.empty()) return;
            cout << "Error: " << msg << ": ";
            int n = 0;
            for (int i : v) {
                cout << i << " ";
                if (n++ > 10) {
                    cout << "...";
                    break;
                }
            }
            cout << endl;
            nerr++;
        };
        report_err(invalid_mo, "invalid nodes in memory order");
        report_err(not_present_mo, "nodes not present in memory order");
        report_err(duplicated_mo, "duplicated nodes in memory order");
        // 1b. Check schedule
        vector<int> node_thread(num_nodes, -1), num_in_thread(num_nodes, -1);
        vector<vector<vector<int>>> syncpt(nthreads, vector<vector<int>>(nthreads, {-1})); // syncpt[i][j] is list of moments in thread i when thread j is waiting for it
        vector<vector<int>> sync_signal_time(sync_points.size(), vector<int>(nthreads, -1)); // sync_signal_time[i][j] is the moment when thread j signals the barrier i
        for (int i = 0; i < nthreads; i++) {
            vector<int> count_syncp(sync_points.size(), 0);
            int prevsync = -1, increase_err = 0;
            int n = 0;
            for (auto [type, j] : schedule[i]) {
                if (type == 0) {
                    if (j >= num_nodes || j < 0) {
                        invalid_sch.push_back(j);
                    } else {
                        count_sch[j]++;
                        node_thread[j] = i;
                        num_in_thread[j] = n;
                    }
                    for (int k = 0; k < nthreads; k++) {
                        syncpt[k][i].push_back(syncpt[k][i].back());
                    }
                } else if (type == 1) {
                    if (prevsync >= j && !increase_err) {
                        cout << "Error: synchronization points are not in increasing order in thread " << i << endl;
                        nerr++;
                        increase_err = 1;
                    }
                    if (j < 0 || j >= sync_points.size()) {
                        invalid_sch.push_back(j);
                    } else {
                        count_syncp[j]++;
                        auto& [wait, signal] = sync_points[j];
                        if (contains(signal, i)) {
                            sync_signal_time[j][i] = n;
                        } else if ( !contains(wait, i)) {
                            cout << "Error: thread " << i << " is not in the list of threads for synchronization point " << j << endl;
                            nerr++;
                        }
                    }
                } else {
                    invalid_sch.push_back(j);
                }
                n++;
            }
            for (int j = 0; j < (int)count_syncp.size(); j++) {
                if (count_syncp[j] > 1) {
                    duplicated_syncp.push_back(j);
                }
            }
            report_err(duplicated_syncp, "duplicated synchronization points in thread " + to_string(i));
        }
        for (int i = 0; i < num_nodes; i++) {
            if (count_sch[i] > 1) {
                duplicated_sch.push_back(i);
            } else if (count_sch[i] == 0 && !deps[i].empty()) {
                not_present_sch.push_back(i);
            }
        }
        report_err(invalid_sch, "invalid nodes in schedule");
        report_err(not_present_sch, "nodes not present in schedule");
        report_err(duplicated_sch, "duplicated nodes in schedule");

        // 2. Check no duplicates and only input nodes in reg_edges
        vector<int> duplicated_re, invalid_re, noninput_re, inconsistent_re;
        vector<int> count_re(num_nodes, 0);
        for (auto [i, j] : reg_edges) {
            if (i >= num_nodes || i < 0 || j >= num_nodes || j < 0) {
                invalid_re.push_back(i);
            } else if (deps[i].empty()) {
                if (node_weights[i] != node_weights[j])
                    inconsistent_re.push_back(i);
                else
                    count_re[i]++;
            } else {
                noninput_re.push_back(i);
            }
        }
        for (size_t i = 0; i < count_re.size(); i++) {
            if (count_re[i] > 1) {
                duplicated_re.push_back(i);
            }
        }
        report_err(inconsistent_re, "inconsistent weights in reg_edges");
        report_err(invalid_re, "invalid nodes in reg_edges");
        report_err(noninput_re, "non-input nodes in reg_edges");
        report_err(duplicated_re, "duplicated nodes in reg_edges");

        // 3. Check sync points
        int syncperr = 0;
        for (size_t i=0; i<sync_points.size(); i++) {
            auto& [wait, signal] = sync_points[i];

            if (any_of(wait.begin(), wait.end(), [this](int i) { return i >= nthreads || i < 0; }) ||
                any_of(signal.begin(), signal.end(), [this](int i) { return i >= nthreads || i < 0; })) {
                syncperr++;
                cout << "Error: invalid thread in sync point: ["<<wait<<", "<<signal<<"]"<<endl;
            } else if (wait.empty() || signal.empty()) {
                syncperr++;
                cout << "Error: empty list in sync point: ["<<wait<<", "<<signal<<"]"<<endl;
            } else if (any_of(signal.begin(), signal.end(), [this, i, &sync_signal_time](int t) { return sync_signal_time[i][t] == -1; })) {
                syncperr++;
                cout << "Error: thread not signaling in sync point: ["<<wait<<", "<<signal<<"]"<<endl;
            }
            if (syncperr > 10) {
                cout << "Error: too many sync point errors; skip further checks" << endl;
                break;
            }
        }
        nerr += syncperr;

        if (nerr) {
            return false;
        }

        // 4. check synchronization correctness (only if no previous errors)
        int nsync_err = 0;
        for (int i = 0; i < nthreads && nsync_err < 10; i++) {
            vector<int> synced(nthreads, -1);
            for (int j = 0; j < (int)schedule[i].size(); j++) {
                auto [type, k] = schedule[i][j];
                if (type == 1) {
                    for (int t : sync_points[k].second) {
                        synced[t] = sync_signal_time[k][t];
                    }
                } else { // type == 0, calculation
                    for (int m : deps[k]) {
                        if (node_thread[m] == i || node_thread[m] == -1) continue; // no need to sync
                        int pos = num_in_thread[m];
                        if (synced[node_thread[m]] < pos) {
                            cout << "Error: in thread " << i << " node "<<k << " using node " << m << " before it is synchronized with thread " << node_thread[m] << endl;
                            nsync_err++;
                        }
                    }
                }
                if (nsync_err >= 10) {
                    cout << "Error: too many sync errors; skip further checks" << endl;
                    break;
                }
            }
        }
        nerr += nsync_err;

        return !nerr;
    }

    void gen_eval_thread(const string& fn, const string& func_name, int thread_id, int start, int end,
                         int& wait_point_i, bool append, /*bool use_templates,*/ const vector<int>& data_start) const {
        ofstream file(fn, append ? ios::app : ios::trunc);
        if (!append) {
            file << "#include \"gen_circuit_impl.h\"\n\n";
            file << "using namespace std;\n\n";
        }
        //file << "void CircuitImpl::eval_"<<thread_id << "() {\n";
        file << "void CircuitImpl::"<<func_name<<"() {\n";
        //int wait_point_i = 0;
        for (int i = start; i < end; i++) {
            auto [type, j] = schedule[thread_id][i];
            if (type == 0) {
                write_expanded_calcP_template(file, j, j, deps[j], data_start);
            } else {
                if (type != 1) throw runtime_error("invalid type "+to_string(type)+" in schedule (expected 0 or 1)");
                if (j < 0 || j >= sync_points.size()) throw runtime_error("invalid sync point "+to_string(j));
                auto& [X, Y] = sync_points[j];
                bool wait = contains(X, thread_id);
                bool notify = contains(Y, thread_id);
                if (notify) file << "    barriers["<<j<<"].notify("<<Y.size()<<");\n";
                if (wait) file << "    barriers["<<j<<"].wait(wait_points["<<thread_id<<"]["<<wait_point_i<<"]);\n";
                wait_point_i += wait;
                if(!notify&&!wait) {
                    throw runtime_error("thread "+to_string(thread_id)+" not in sync point "+to_string(j));
                }
            }
        }
        file << "}\n";
    }
    void write_expanded_calcP_template(ostream& file, int node, int S, const vector<int>& args, const vector<int>& data_start) const {
        /* Inline the calc_P function call:
         * template<int W> class Node {
            ...
            template<int S, int start>
            void _calc_P() {}
            template<int S, int start, int W1, int ... Ws>
            void _calc_P(const Node<W1>& n1, const Node<Ws>& ... args) {
                for (int i = 0; i < W1; i++) {
                    data[(i+start)%W] += n1.data[i]*S;
                }
                _calc_P<(S>>2)*7 | 1, (start+W1)%W>(args...);
            }
            template<int S, int ... Ws>
            void calc_P(const Node<Ws>& ... args) {
                _calc_P<S*2 + 1, 0>(args...);
            }
            };*/
        int start = 0, W = node_weights[node];
        S = S*2 + 1;
        for (int arg : args) {
            int W1 = node_weights[arg];
            for (int j = 0; j < W1; j++) {
                file << "    state.data["<<data_start[node] + (j+start)%W<<"] += state.data["<<(data_start[arg]+j)<<"]*" << S << ";\n";
            }
            S = (S>>2)*7 | 1;
            start = (start+W1)%W;
        }
    }
    void gen_code(const string &fn, int maxChunkSize/*, bool use_templates*/) const {
        vector<string> node_names(num_nodes);
        ofstream file(fn+"_impl.h"), cppfile(fn+".cpp");
        file << "#include \"circuit.h\"\n";
        file << "#include <thread>\n";
        file << "#include \"synchronize.h\"\n\n";
        file << "struct CircuitImpl : public Circuit {\n";
        file << "    SpinLockWait barriers["<<sync_points.size()<<"];\n";
        file << "    vector<int> wait_points["<<nthreads<<"];\n";
        vector<int> data_start(num_nodes,0);
        int total_weight = 0;
        for (int i = 0; i < num_nodes; i++) {
            int node_id = mem_order[i];
            data_start[node_id] = total_weight;
            total_weight += node_weights[node_id];
        }
        file << "    struct State {\n";
        file << "        uint32_t data["<<total_weight<<"];\n";
        file << "    } state;\n";

        int maxFiles = max<int>(1, std::thread::hardware_concurrency()*2);
        vector<bool> used(maxFiles, false);
        int curr_file = 0;
        for (int i = 0; i < nthreads; i++) {
            int wait_point = 0, size = int(schedule[i].size());
            if (maxChunkSize && maxChunkSize < size) {
                int nchunks = (size + maxChunkSize - 1) / maxChunkSize;
                stringstream evalfunc;
                evalfunc << "    void eval_"<<i<<"() {\n";
                for (int j = 0; j < nchunks; j++) {
                    auto start = j * maxChunkSize, end = min((j + 1) * maxChunkSize, size);
                    string funcname = "eval_" + to_string(i) + "_chunk_" + to_string(j);
                    file << "    void " << funcname << "();\n";
                    evalfunc << "        " << funcname << "();\n";
                    gen_eval_thread(fn+"_eval_part"+to_string(curr_file)+".cpp", funcname, i, start, end, wait_point, used[curr_file], data_start);//, use_templates);
                    used[curr_file] = true;
                    curr_file = (curr_file + 1) % maxFiles;
                }
                evalfunc << "    }\n";
                file << evalfunc.str();
            } else {
                file << "    void eval_"<<i<<"();\n";
                gen_eval_thread(fn+"_eval"+ to_string(i)+".cpp", "eval_"+to_string(i), i, 0, size, wait_point, false, data_start);//, use_templates);
            }
        }
        file << "    CircuitImpl() {\n";
        for (int i=0; i<nthreads; i++) {
            int num_wait_points = std::count_if(schedule[i].begin(), schedule[i].end(), [this, i](auto p) {
                return p.first == 1 && contains(sync_points[p.second].first, i);
            });
            file << "        wait_points["<<i<<"].resize("<<num_wait_points<<", 0);\n";
        }
        file << "    }\n";

        file << "    int num_threads() override { return " << nthreads << "; }\n";
        file << "    int num_nodes() override { return " << num_nodes << "; }\n";

        file << "    void eval(int thread_id) override {\n";
        file << "        switch(thread_id) {\n";
        for (int thread_id = 0; thread_id < nthreads; thread_id++) {
            file << "            case " << thread_id << ": return eval_" << thread_id << "();\n";
        }
        file << "        }\n";
        file << "    }\n";
        file << "};\n";

        cppfile << "#include \"gen_circuit_impl.h\"\n\n";
        cppfile << "unique_ptr<Circuit> create_circuit() {\n";
        cppfile << "    return make_unique<CircuitImpl>();\n";
        cppfile << "}\n";
        //for (int i = 0; i < nthreads; i++) {
        //    gen_eval_thread(fn + "_eval" + to_string(i) + ".cpp", i);
        //}
    }
};


int run(int argc, char *argv[]) {
    // argv[1] is the input JSON file
    // argv[2] is the temporary directory to write the generated code
    // options:
    Options options = {
        {"output", "o", JSON::String, "Output file for test results (used with -r); if not specified, output to stdout", ""},
        {"verbose", "v", JSON::Boolean, "Verbose output", false},
        {"run", "r", JSON::Boolean, "Run the generated code", false},
        {"chunk-size", "", JSON::Integer, "Maximum number of rows in one evaluation function chunk", 1000},
        {"debug", "d", JSON::Boolean, "Compile generated code with debug flags", false},
        {"rebuild", "B", JSON::Boolean, "Clean the build directory before generating code", false},
        {"compiler", "c", JSON::String, "C++ compiler to use", ""},
        //{"profile", "p", JSON::Boolean, "Compile generated code with profiling flags (e.g. -pg)", false},
        {"time", "t", JSON::Double, "Test running time (in seconds)", 1.0},
        {"help", "h", JSON::Boolean, "Print this help message", false},
    };
    Options positionalArgs = {
        {"input", "", JSON::String, "Input JSON file"},
        {"output_path", "", JSON::String, "Path to output directory"},
    };
    JSON time_results(JSON::Object);
    JSON args;
    try {
        args = parseCmd(argc, argv, positionalArgs, options);
        if (args["help"].as<bool>()) {
            printUsage(argv[0], positionalArgs, options, "Circuit simulation speed test", true);
            return 0;
        }
    } catch (const std::runtime_error& e) {
        cerr << "Error: " << e.what() << endl;
        printUsage(argv[0], positionalArgs, options);
        return 1;
    }

    bool verbose = args["verbose"].as<bool>();
    if (verbose) {
        cout << "Running with args: " << args << endl;
    }

    auto input_file = args["input"].str();
    Timer timer;
    auto input = JSON::load(input_file);
    if (verbose)
        cout << "Load time: " << timer.getTime() << " s" << endl;
    time_results["load_time"] = timer.getTime();
    timer.reset();
    CircuitGraph graph(input);
    if (verbose) {
        cout << "Graph initialization time: " << timer.getTime() << " s" << endl;

        cout << "Number of nodes: " << graph.num_nodes << endl;
        cout << "Number of regs: " << graph.reg_edges.size() << endl;
    }
    time_results["graph_init_time"] = timer.getTime();
    timer.reset();
    bool correct = graph.checkCorrectness();
    if (verbose) {
        cout << "Correctness check time: " << timer.getTime() << " s" << endl;
        cout << "Correctness: " << correct << endl;
    }
    time_results["correctness_check_time"] = timer.getTime();
    if (!correct) {
        cout << "Graph is not correct" << endl;
        return 1;
    }

    auto work_path = args["output_path"].str();
    int maxChunkSize = args["chunk-size"].as<int>();
    if (work_path.empty()) {
        work_path = ".";
    }
    if (work_path.back() != '/') {
        work_path += "/";
    }
    string output_path = work_path + "generated_code/";
    string src_root = rootPath();
    // create directory and copy files from src_root/simulation/simfiles and src_root/utils to output_path
    string simfiles_path = src_root + "simulation/simfiles";
    string utils_path = src_root + "utils";

    if (verbose) {
        cout << "Copying files from " << simfiles_path << " to " << output_path << endl;
    }
    std::filesystem::create_directories(output_path);
    // clear the directory
    bool clean_all = args["rebuild"].as<bool>();
    for (const auto &entry : std::filesystem::directory_iterator(output_path)) {
        // remove files starting with "gen_"
        if (entry.path().filename().string().substr(0, 4) == "gen_" || clean_all)
            std::filesystem::remove_all(entry.path());
    }

    for (const auto &entry : std::filesystem::directory_iterator(simfiles_path)) {
        string filename = entry.path().filename();
        if (verbose) {
            cout << "Copying " << filename << endl;
        }
        std::filesystem::copy(entry.path(), output_path + filename, std::filesystem::copy_options::overwrite_existing);
    }
    if (verbose) {
        cout << "Copying files from " << utils_path << " to " << output_path << endl;
    }
    for (const auto &entry : std::filesystem::directory_iterator(utils_path)) {
        // copy only the .h files
        string filename = entry.path().filename();
        if (filename.size() <= 2 || filename.substr(filename.size()-2) != ".h") {
            continue;
        }
        if (verbose) {
            cout << "Copying " << filename << endl;
        }
        std::filesystem::copy(entry.path(), output_path + filename, std::filesystem::copy_options::overwrite_existing);
    }
    // generate the code
    timer.reset();
    graph.gen_code(output_path+"gen_circuit", maxChunkSize);//, !args["no-templates"].as<bool>());
    if (verbose) {
        cout << "Code generation time: " << timer.getTime() << " s" << endl;
    }
    time_results["gen_code_time"] = timer.getTime();

    if(!args["run"].as<bool>()) {
        return 0;
    }
    timer.reset();
    // compile the code using cmake in output_path/build
    string build_path = output_path + "build";
    std::filesystem::create_directories(build_path);
    string cmake_cmd = "cmake -S \"" + output_path + "\" -B \"" + build_path + "\"";
    if (args["debug"].as<bool>()) {
        cmake_cmd += " -DCMAKE_BUILD_TYPE=Debug";
    } else {
        cmake_cmd += " -DCMAKE_BUILD_TYPE=Release";
    }
    if (!args["compiler"].str().empty()) {
        cmake_cmd += " -DCMAKE_CXX_COMPILER=" + args["compiler"].str();
    }

    int jthreads = 0;
    // if Ninja is available, use it
    if (system("ninja --version 2> " NULL_OUTPUT "> " NULL_OUTPUT) == 0) {
        cmake_cmd += " -G Ninja";
    } else {
#if defined(__linux__) || defined(__APPLE__) || defined(__gcc__)
        jthreads = std::thread::hardware_concurrency()-1;
#endif
    }
    if (verbose) {
        cout << "Running: " << cmake_cmd << endl;
    } else {
        cmake_cmd += " 2> " NULL_OUTPUT " > " NULL_OUTPUT;
    }
    int ret = system(cmake_cmd.c_str());
    if (ret != 0) {
        cerr << "Error: cmake failed with return code " << ret << endl;
        return ret;
    }
    time_results["cmake_time"] = timer.getTime();

    string make_cmd = "cmake --build \"" + build_path + "\"";
    if (args["debug"].as<bool>()) {
        make_cmd += " --config Debug";
    } else {
        make_cmd += " --config Release";
    }
    if (jthreads > 1) {
        make_cmd += " -- -j" + to_string(jthreads);
    }
    if (verbose) {
        cout << "Running: " << make_cmd << endl;
    } else {
        make_cmd += " 2> " NULL_OUTPUT " > " NULL_OUTPUT;
    }

    timer.reset();
    ret = system(make_cmd.c_str());
    if (ret != 0) {
        cerr << "Error: make failed with return code " << ret << endl;
        return ret;
    }
    if (verbose) {
        cout << "Compilation time: " << timer.getTime() << " s" << endl;
    }
    time_results["compilation_time"] = timer.getTime();
    // run the code
    string executable = output_path + "/bin/simulator";
    auto timeout = args["time"].as<double>();
    timer.reset();
    string run_cmd = executable + " " + to_string(timeout);
    string output_json = args["output"].str();
    if (!output_json.empty()) {
        output_json = work_path + output_json;
        run_cmd += " \"" + output_json + "\"";
    }
    if (verbose) {
        cout << "Running: " << run_cmd << endl;
    }
    if (verbose) {
        cout << "==================== Running the simulator ====================" << endl;
    }
    ret = system(run_cmd.c_str());
    if (verbose) {
        cout << "====================   Simulator finished  ====================" << endl;
    }
    if (ret != 0) {
        cerr << "Error: simulator failed with return code " << ret << endl;
        return ret;
    }
    if (verbose) {
        cout << "Running time: " << timer.getTime() << " s" << endl;
    }
    if (!output_json.empty()){
        if (verbose) {
            cout << "Output written to " << output_json << ": " << endl;
        }
        cout<<"{"<<endl;
        cout << "stages_time: " << time_results.toString(true) << "," << endl;
        ifstream file(output_json);

        cout << "run_results: " << file.rdbuf();
        cout<<"}"<<endl;
    }
    return 0;
}

int main(int argc, char *argv[]) {
    try {
        return run(argc, argv);
    } catch (const std::exception &e) {
        cerr << "Exception: " << e.what() << endl;
        return 1;
    }
}
