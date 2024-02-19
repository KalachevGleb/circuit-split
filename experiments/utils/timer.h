#pragma once
#include <chrono>

class Timer {
    std::chrono::time_point<std::chrono::high_resolution_clock> _lastCheck;
public:
    Timer() {
        reset();
    }
    double getTime(bool reset = false) {
        auto current = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> elapsed = current - _lastCheck;
        if (reset) _lastCheck = current;
        return elapsed.count();
    }
    void reset() {
        getTime(true);
    }
};
