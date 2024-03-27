#include "argparse.h"
#include "timer.h"

#include <random>
#include <iostream>
#include <vector>
#include <iomanip>
#include <ranges>

using namespace std;


uint32_t test_sequential(const vector<uint32_t>& x) {
    uint32_t sum = 0;
    for (auto i : x) {
        sum += i;
    }
    return sum;
}

template<int depth, int n, size_t d>
uint32_t test_reverse_order_ND(const uint32_t* x) {
    if constexpr(depth == 0) {
        return x[0];
    } else if constexpr(depth == 1) {
        uint32_t sum = 0;
        for (int i = 0; i < n; i++) {
            sum += x[i*d];
        }
        return sum;
    } else {
        uint32_t sum = 0;
        for (int i = 0; i < n; i++) {
            sum += test_reverse_order_ND<depth - 1, n, d*n>(x + i * d);
        }
        return sum;
    }
}
uint32_t test_order(const vector<uint32_t>& x, const vector<uint32_t>& order) {
    uint32_t sum = 0;
    for (auto i : order) {
        sum += x[i];
    }
    return sum;
}
vector<uint32_t> seq_order(int n) {
    vector<uint32_t> order(n);
    for (int i = 0; i < n; i++) {
        order[i] = i;
    }
    return order;
}
vector<uint32_t> random_order(int n, int seed) {
    vector<uint32_t> order = seq_order(n);
    mt19937 gen(seed);
    shuffle(order.begin(), order.end(), gen);
    return order;
}

uint32_t reverse_bits(int x, int n) {
    uint32_t y = 0;
    for (int i = 0; i < n; i++) {
        y = (y << 1) | (x & 1);
        x >>= 1;
    }
    return y;
}
vector<uint32_t> bitreverse_order(int n) {
    int nbits = int(round(log2(1.0*n)));
    if (n != 1 << nbits) {
        throw invalid_argument("n must be a power of 2");
    }
    vector<uint32_t> order(n);
    for (int i = 0; i < n; i++) {
        order[i] = reverse_bits(i, nbits);
    }
    return order;
}

template<int depth>
uint32_t test_reverse_order_D(const vector<uint32_t>& x, int n) {
    switch(n) {
        case 2:
            return test_reverse_order_ND<depth, 2, 1>(x.data());
        case 3:
            return test_reverse_order_ND<depth, 3, 1>(x.data());
        case 4:
            return test_reverse_order_ND<depth, 4, 1>(x.data());
        case 5:
            return test_reverse_order_ND<depth, 5, 1>(x.data());
        case 6:
            return test_reverse_order_ND<depth, 6, 1>(x.data());
        case 7:
            return test_reverse_order_ND<depth, 7, 1>(x.data());
        case 8:
            return test_reverse_order_ND<depth, 8, 1>(x.data());
        default:
            throw runtime_error("Unsupported n");
    }
}

uint32_t test_reverse_order(const vector<uint32_t>& x, int n) {
    double ddepth = log(x.size())/log(n);
    int depth = (int)round(ddepth);
    if(pow(n, depth) != x.size())
        throw runtime_error("Invalid input size: " + to_string(x.size()) + " " + to_string(n) + " " + to_string(depth));
    switch(depth) {
        case 0:
            return test_reverse_order_D<0>(x, n);
        case 1:
            return test_reverse_order_D<1>(x, n);
        case 2:
            return test_reverse_order_D<2>(x, n);
        case 3:
            return test_reverse_order_D<3>(x, n);
        case 4:
            return test_reverse_order_D<4>(x, n);
        case 5:
            return test_reverse_order_D<5>(x, n);
        case 6:
            return test_reverse_order_D<6>(x, n);
        case 7:
            return test_reverse_order_D<7>(x, n);
        case 8:
            return test_reverse_order_D<8>(x, n);
        case 9:
            return test_reverse_order_D<9>(x, n);
        case 10:
            return test_reverse_order_D<10>(x, n);
        case 11:
            return test_reverse_order_D<11>(x, n);
        case 12:
            return test_reverse_order_D<12>(x, n);
        case 13:
            return test_reverse_order_D<13>(x, n);
        case 14:
            return test_reverse_order_D<14>(x, n);
        case 15:
            return test_reverse_order_D<15>(x, n);
        case 16:
            return test_reverse_order_D<16>(x, n);
        case 17:
            return test_reverse_order_D<17>(x, n);
        case 18:
            return test_reverse_order_D<18>(x, n);
        case 19:
            return test_reverse_order_D<19>(x, n);
        case 20:
            return test_reverse_order_D<20>(x, n);
        case 21:
            return test_reverse_order_D<21>(x, n);
        case 22:
            return test_reverse_order_D<22>(x, n);
        case 23:
            return test_reverse_order_D<23>(x, n);
        case 24:
            return test_reverse_order_D<24>(x, n);
        default:
            throw runtime_error("Unsupported depth");
    }
}


tuple<double,double,double, double> benchmark_indexed(int n, int seed, double tmax=1) {
    mt19937 gen(seed);
    vector<uint32_t> x(n);
    for (size_t i = 0; i < n; i++) {
        x[i] = gen();
    }
    Timer timer;
    double t = 0;
    int iter = 0;
    volatile uint32_t sum = 0;
    auto order = seq_order(n);
    cout<< "test n = " << n << endl;
    timer.reset();
    t = 0;
    iter = 0;
    for(;t<tmax;iter++) {
        sum = sum * test_sequential(order);
        t = timer.getTime();
    }
    double t_read = (t/iter/n)*1e9;
    cout << "Index array read: " << t_read << " ns" << endl;

    timer.reset();
    t = 0;
    iter = 0;
    for(;t<tmax;iter++) {
        sum = sum * test_order(x, order);
        t = timer.getTime();
    }
    double t_seq = (t/iter/n)*1e9;
    cout << "Sequential order:  " << (t_seq - t_read) << " ns (" << t_seq << " ns)" << endl;

    order = random_order(n, seed);
    timer.reset();
    t = 0;
    iter = 0;
    for(; t<tmax; iter++) {
        sum = sum * test_order(x, order);
        t = timer.getTime();
    }
    double t_random = (t/iter/n)*1e9;
    cout << "Random order:      " << (t_random - t_read) << " ns (" << t_random << " ns)" << endl;

    order = bitreverse_order(n);
    timer.reset();
    t = 0;
    iter = 0;
    for(; t<tmax; iter++) {
        sum = sum * test_order(x, order);
        t = timer.getTime();
    }
    double t_bitrev = (t/iter/n)*1e9;
    cout << "Bit-reversed order: " << (t_bitrev - t_read) << " ns (" << t_bitrev << " ns)" << endl;


    return {t_read, (t_seq-t_read), (t_random-t_read), (t_bitrev-t_read)};
}

double benchmark_nd(int n, int depth, double tmax=1) {
    mt19937 gen(0);
    auto size = (size_t)pow(n, depth);
    vector<uint32_t> x(size);
    for (size_t i = 0; i < size; i++) {
        x[i] = gen();
    }
    Timer timer;
    double t = 0;
    int iter = 0;
    volatile uint32_t sum = 0;
    cout<< "test n = " << n << " depth = " << depth << endl;
    for(;t<tmax;iter++) {
        sum = sum * test_reverse_order(x, n);
        t = timer.getTime();
    }
    double t_reverse = t/iter;
    cout << "Reverse order:  " << t_reverse << " s" << endl;

    timer.reset();
    t = 0;
    iter = 0;
    for(;t<tmax;iter++) {
        sum = sum * test_sequential(x);
        t = timer.getTime();
    }
    double t_order = t/iter;
    cout << "Sequential order: " << t_order << " s" << endl;
    return t_reverse/t_order;
}

void test_indexed(int logn_min, int logn_max, double tmax) {
    map<int, tuple<double,double,double,double>> res;
    for (int logn = logn_min; logn <= logn_max; logn++) {
        auto [t_read, t_seq, t_random, t_bitrev] = benchmark_indexed(1<<logn, 0, tmax);
        res[logn] = {t_read, t_seq, t_random, t_bitrev};
    }
    // print results as a Python dictionary
    cout << "results = {" << endl;
    cout << "    \"sizes\": [";
    for (auto& [logn, r] : res) {
        cout << (1<<logn) << ", ";
    }
    cout << "]," << endl;
    cout << "    \"read\": [";
    for (auto& [logn, r] : res) {
        cout << get<0>(r) << ", ";
    }
    cout << "]," << endl;
    cout << "    \"seq\": [";
    for (auto& [logn, r] : res) {
        cout << get<1>(r) << ", ";
    }
    cout << "]," << endl;
    cout << "    \"random\": [";
    for (auto& [logn, r] : res) {
        cout << get<2>(r) << ", ";
    }
    cout << "]," << endl;
    cout << "    \"worst\": [";
    for (auto& [logn, r] : res) {
        cout << get<3>(r) << ", ";
    }
    cout << "]," << endl;
    cout << "}" << endl;

    // print results in a markdown table format, column width = 10, .2f format, size in KB
    cout << "| Size (KB) |  Read (ns) |  Seq (ns)  | Random (ns) | Bitrev (ns) |" << endl;
    cout << "|-----------|------------|------------|-------------|-------------|" << endl;
    // save flags
    auto flags = cout.flags();
    for (auto& [logn, r] : res) {
        auto [t_read, t_random, t_seq,t_bitrev] = r;
        cout << "| " << setw(9) << fixed << setprecision(2) << (1<<logn)/256 <<
               " | " << setw(10) << fixed << setprecision(2) << t_read <<
               " | " << setw(10) << fixed << setprecision(2) << t_seq <<
               " | " << setw(11) << fixed << setprecision(2) << t_random <<
               " | " << setw(11) << fixed << setprecision(2) << t_bitrev << " |" << endl;
    }
    cout.flags(flags);

}

void test_n_d(int n, int dmin, int dmax) {
    map<int, double> ratios;
    for (int d = dmin; d <= dmax; d++) {
        ratios[d] = benchmark_nd(n, d);
    }
    cout<< "===============================" << endl;
    cout << "n = " << n << endl;
    for (auto& [d, r] : ratios) {
        cout << "size = " << 4*pow(n, d)*1e-3 << " KB:\t  speedup = " << r << endl;
    }
}

int main(int argc, const char** argv) {
    //test_n_d(2, 8, 24);
    //test_n_d(4, 4, 12);
    test_indexed(8, 24, 10);
    return 0;
}

