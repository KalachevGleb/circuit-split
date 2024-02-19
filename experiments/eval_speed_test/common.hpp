#ifndef EVAL_SPEED_TEST_COMMON_HPP
#define EVAL_SPEED_TEST_COMMON_HPP

#include <vector>
#include <string>
#include <chrono>

#include "semaphore.hpp"
#include "defines.hpp"

std::vector<int> split_string(std::string str);

#ifdef PROFILE_SEMAPHORE
class SemaphoreProfiler {
    long sema_time;
    long real_time;

    long sema_start;
    std::chrono::time_point<std::chrono::high_resolution_clock> real_start;

    bool running;
public:
    SemaphoreProfiler() : sema_time(0), real_time(0), running(false) {}

    void start() {
        if(running) throw 1;
        running = true;

        sema_start = LightweightSemaphore::uptime();
        real_start = std::chrono::high_resolution_clock::now();
    }

    void stop() {
        if(!running) throw 1;
        running = false;

        sema_time += LightweightSemaphore::uptime() - sema_start;
        real_time += std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::high_resolution_clock::now() - real_start).count();
    }

    void reset() {
        if(running) stop();

        sema_time = 0;
        real_time = 0;
    }

    long get_sema_time() {
        return sema_time;
    }

    long get_real_time() {
        return real_time;
    }
};
#endif

#endif