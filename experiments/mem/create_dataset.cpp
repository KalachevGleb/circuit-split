#include <iostream>
#include <chrono>
#include <cstdlib>
#include <vector>

using namespace std;

const int MEM_SIZE = 600000;
const int DATASET_SIZE = 5000;
const int ROLLOUT_SIZE = 10000;

struct Experiment {
    Experiment(int _a, int _b, double _time) : a(_a), b(_b), time(_time) {};

    int a;
    int b;
    int time;
};

int main() {
    vector<Experiment> results;

    auto mem = new char[MEM_SIZE];

    for(int i = 0; i < DATASET_SIZE; ++i) {
        int a = rand() % MEM_SIZE;
        int b = rand() % MEM_SIZE;

        auto start = std::chrono::high_resolution_clock::now();
        for(int j = 0; j < ROLLOUT_SIZE; ++j) {
            mem[a] += mem[b];
        }
        auto stop = std::chrono::high_resolution_clock::now();
        int time = std::chrono::duration_cast<std::chrono::nanoseconds>(stop - start).count();

        results.push_back(Experiment(a, b, time));
    }

    FILE* fd = fopen("dataset.csv", "w");
    for(auto& res: results) {
        fprintf(fd, "%d, %d, %d\n", res.a, res.b, res.time);
    }
    fclose(fd);

    return 0;
}