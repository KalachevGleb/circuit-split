#include <iostream>
#include <fstream>
#include <string>
#include <vector> 
#include <thread>

#include <ctime>
#include <cstdlib>

#include "semaphore.hpp"
#include "common.hpp"

using namespace std;

const char input_path[] = "cut.txt";
const int RUN_COUNT = 50;

/* TODO
Использовать std::chrono::high_resolution_clock()
Убрать лишний вывод в консоль
Комментарии
*/

struct Line {
    int thread;
    int index;
    int weight;
    vector<int> forward_deps, sync_deps;

    Line(string args) {
        auto contents = split_string(args);

        thread = contents[0];
        index = contents[1];
        weight = contents[2];

        if(contents.size() > 3) {
            for(auto dep: vector<int>(contents.begin() + 3, contents.end())) {
                if(dep < 0) sync_deps.push_back(-dep - 1);
                else forward_deps.push_back(dep);
            }
        }
    }

private:
    Line() = delete;
};

void worker(const vector<Line*> lines,
            const vector<Semaphore*> Semaphores,
            const int thread,
            const Semaphore* start_sema_1,
            const Semaphore* start_sema_2,
            const vector<int> queue_size) {

    auto line_queue = vector<Line*>();
    for(auto line_ptr: lines)  {
        if(line_ptr -> thread == thread) {
            line_queue.push_back(line_ptr);
        }
    }

    int x = rand();
    int y = rand();

    start_sema_1 -> signal();
    start_sema_2 -> wait();

    int queue_len = line_queue.size();
    for(int line_iter = 0; line_iter < queue_len; ++line_iter) {
        auto line_ptr = line_queue[line_iter];

        int len_dep = (line_ptr -> sync_deps).size();
        for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
            int dep = (line_ptr -> sync_deps)[dep_iter];

            Semaphores[dep] -> wait();

            for(int i = 0; i < lines[dep] -> weight; ++i) {
                y = x;
                x = y;
            }
        }
        
        len_dep = (line_ptr -> forward_deps).size();
        for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
            int dep = (line_ptr -> forward_deps)[dep_iter];

            for(int i = 0; i < lines[dep] -> weight; ++i) {
                y = x;
                x = y;
            }
        }

        int q = queue_size[line_ptr -> index];
        if(q > 0) {
            Semaphores[line_ptr -> index] -> signal(q);
        }
    }

    printf("Trash: %d %d\n", x, y);

    return;
}

int main() {
    printf("Reading\n");

    ifstream fd;
    fd.open(input_path, ios_base::in);

    string read_buff;
    vector<Line*> lines;
    if (fd.is_open()) {
        while (fd) {
            getline(fd, read_buff);

            if(split_string(read_buff).size() == 0) continue;

            lines.push_back(new Line(read_buff));
        }
    }

    fd.close();

    printf("%lu lines read\n", lines.size());

    int max_thread = -1;
    for(auto line_ptr: lines) {
        if(line_ptr -> thread > max_thread) max_thread = line_ptr -> thread;
    }
    int thread_count = max_thread + 1;

    printf("Thread count: %d\n", thread_count);

    vector<int> queue_size(lines.size(), 0);
    for(auto line_ptr: lines) {
        for(auto dep: line_ptr -> sync_deps) {
                ++queue_size[dep];
        }
    }

    vector<clock_t> results;

    for(int run = 0; run < RUN_COUNT; ++run) {
        

        auto Semaphores = vector<Semaphore*>();
        for(auto q: queue_size) {
            if(q > 0) {
                Semaphores.push_back(new Semaphore);
            }
            else {
                Semaphores.push_back(nullptr);
            }
        }

        vector<thread*> thread_pool(thread_count, nullptr);
        Semaphore start_sema_1(thread_count);
        Semaphore start_sema_2(thread_count);

        for(int t = 0; t < thread_count; ++t) {
            thread_pool[t] = new thread(worker, lines, Semaphores, t, &start_sema_1, &start_sema_2, queue_size);
        }

        for(int t = 0; t < thread_count; ++t) {
            start_sema_1.wait();
        }

        auto start = clock();
        
        for(int t = 0; t < thread_count; ++t) {
            start_sema_2.signal();
        }

        for(int t = 0; t < thread_count; ++t) {
            thread_pool[t] -> join();
        }

        auto stop = clock();

        results.push_back(stop - start);

        for(int t = 0; t < thread_count; ++t) {
            delete thread_pool[t];
        }

        for(auto sema_ptr: Semaphores) {
            if(sema_ptr != nullptr) {
                delete sema_ptr;
            }
        }
    }

    for(auto line_ptr: lines) {
        delete line_ptr;
    }

    long sum = 0;
    for(int i = 0; i < RUN_COUNT; ++i) sum = sum + results[i];

    printf("Mean time: %3.4lfs, mean ticks: %u\n", static_cast<double>(sum) / (RUN_COUNT * CLOCKS_PER_SEC), static_cast<unsigned int>(sum / RUN_COUNT));

    return 0;
}