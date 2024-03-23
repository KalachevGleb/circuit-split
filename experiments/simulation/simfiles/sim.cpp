#include "node.h"
#include "circuit.h"
#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char** argv) {
    // Usage: ./sim <time in seconds> [output file]
    if (argc < 2 || argc > 3) {
        std::cerr << "Usage: ./sim <time in seconds> [output file]"<< std::endl;
        return 1;
    }
    double time = std::stod(argv[1]);
    string output;
    ofstream out;
    ostream *pout = &cout;
    if (argc == 3) {
        output = argv[2];
        out.open(output);
        pout = &out;
    }
    Simulation sim;
    auto [nsteps, total_time, s_per_node, s_per_read] = sim.run(time);
    // output in JSON format
    *pout << "{\n";
    *pout << "  \"nsteps\": " << nsteps << ",\n";
    *pout << "  \"total_time\": " << total_time << ",\n";
    *pout << "  \"steps_per_second\": " << nsteps / total_time << ",\n";
    *pout << "  \"time_per_step\": " << total_time / nsteps << ",\n";
    *pout << "  \"ns_per_node\": " << s_per_node*1e9 << ",\n";
    *pout << "  \"ns_per_read\": " << s_per_read*1e9 << "\n";
    *pout << "}\n";
    return 0;
}
