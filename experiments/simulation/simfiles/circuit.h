#pragma once
#include <vector>
#include <thread>
#include <memory>

#include "synchronize.h"
#include "timer.h"
//#include "node.h"

using namespace std;

struct Circuit { // abstract class for circuit simulation
    WorkerNotifier<bool> worker_notifier;

    virtual int num_threads() = 0;
    virtual int num_nodes() = 0;
    virtual int num_reads() = 0;
    virtual void eval(int thread_id) = 0;
    virtual ~Circuit() = default;
    void next_clock() {
        worker_notifier.main_notify(true);
        worker_notifier.main_wait();
    }
    void stop(vector<thread> &threads) {
        worker_notifier.main_notify(false);
        for (auto &thread : threads) {
            thread.join();
        }
        threads.clear();
    }
    void run(int thread_id) {
        int n = num_threads();
        while (worker_notifier.worker_sync(n)) {
            eval(thread_id);
        }
    }
    void start(vector<thread> &threads) {
        if (!threads.empty()) {
            throw runtime_error("threads should be empty");
        }
        int n = num_threads();
        for (int i = 0; i < n; i++) {
            threads.emplace_back([this, i] { run(i); });
        }
        worker_notifier.main_wait();
    }
};

unique_ptr<Circuit> create_circuit(); // to be defined in generated code (simfiles/circuit.cpp will be generated for given circuit)


class Simulation {
    vector<thread> threads;
    unique_ptr<Circuit> circuit;
    int num_threads;
public:
    Simulation() : circuit(create_circuit()), num_threads(circuit->num_threads()) {}

    tuple<int, double, double, double> run(double time) {
        int numNodes = circuit->num_nodes(), numReads = circuit->num_reads();
        circuit->start(threads);
        int n = 0;
        Timer timer;
        while (timer.getTime() < time) {
            circuit->next_clock();
            n++;
        }
        double total_time = timer.getTime();
        circuit->stop(threads);
        return {n, total_time, total_time / n / numNodes, total_time / n / numReads};
    }
};
