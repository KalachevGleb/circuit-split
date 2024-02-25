#include <iostream>
#include <fstream>
#include <string>
#include <vector> 
#include <thread>
#include <chrono>

#include <ctime>
#include <cstdlib>

#include "semaphore.hpp"
#include "common.hpp"
#include "defines.hpp"
#include "line.hpp"
#include "worker.hpp"

using namespace std;

const char INPUT_PATH[] = "cut.txt";                    //См описание структуры Line

/*
Нужно что-то быстрее семафора
Надо попробовать не степень двойки потоков
Надо попробовать LightweightSemaphore на сервере
*/

/* TODO
*/

/*
Этот класс - представление строки из целых чисел, описывающее
    очередную вершину из обхода графа, сгенерированного gen.py

Оно устроено следующим образом:

номер потока
номер вершины, должен совпадать с номером строки, он здесь для
    удобства
вес вершины
последовательность вершин, от которых зависит данная, а именно
    если родитель лежит в том же потоке, что и текущая вершина,
        то указывается его номер вершины, т.е. номер его
        строки
    если родитель и текущая вершина лежат в разных потоках,
        то указывается минус номер вершины родителя
        минус один
    то есть это число однозначно кодирует информацию о
        типе зависимости относительно потока
        (внешняя/внутренняя) и о номере родителя
*/


vector<uint64_t> main_routine(const char* input_path) {
    // ====================================================== //
    // Чтение //
    // ====================================================== //

    #ifdef STATUS_PRINT
    printf("Reading\n");                                            //Чтение из cut.txt
    #endif

    ifstream fd;
    fd.open(input_path, ios_base::in);

    string read_buff;
    vector<const Line*> lines;
    if (fd.is_open()) {
        while (fd) {
            getline(fd, read_buff);

            if(split_string(read_buff).size() == 0) continue;       

            lines.push_back(new Line(read_buff));
        }
    }

    fd.close();

    #ifdef STATUS_PRINT
    printf("%lu lines read\n", lines.size());
    #endif

    // ====================================================== //
    // Статистика по прочитанному //
    // ====================================================== //

    int max_thread = -1;                                                                    //Вычисляем реальное число потоков, т.к. gen.py может не использовать часть из них
    for(auto line_ptr: lines) {
        if(line_ptr -> thread > max_thread) max_thread = line_ptr -> thread;
    }
    int thread_count = max_thread + 1;

    #ifdef STATUS_PRINT
    printf("Thread count: %d\n", thread_count);
    #endif                                             

    vector<int> queue_size(lines.size(), 0);                                                //Массив, определяющий число вешнин из других потоков, зависящих от данной
    for(auto line_ptr: lines) {
        for(auto dep: line_ptr -> sync_deps) {
                ++queue_size[dep];
        }
    }

    // ====================================================== //
    // Вычисления //
    // ====================================================== //

    vector<uint64_t> results;
    if (thread_count != 1) {

        // ====================================================== //
        // Подготовка //
        // ====================================================== //

        Semaphore start_sema_1(thread_count);
        Semaphore start_sema_2(thread_count);  
        Semaphore end_sema(thread_count);
        
        auto semaphores = vector<const Semaphore*>();
        for(auto q: queue_size) {                                                               
            if(q > 0) {
                semaphores.push_back(new Semaphore);
            }
            else {
                semaphores.push_back(nullptr);
            }
        }

        vector<thread*> thread_pool(thread_count, nullptr); 
        for(int t = 0; t < thread_count; ++t) {
            thread_pool[t] = new thread(pretty_worker, lines, semaphores, t, &start_sema_1, &start_sema_2, &end_sema, queue_size);
        }

        // ====================================================== //
        // Прогон в цикле //
        // ====================================================== //

        auto start = std::chrono::high_resolution_clock::now();

        #ifdef PROFILE_SEMAPHORE
        SemaphoreProfiler compute_loop_profiler;
        compute_loop_profiler.start();
        #endif

        for(int run = 0; run < RUN_COUNT; ++run) {
            for(int t = 0; t < thread_count; ++t) {
                start_sema_1.wait();
            }
            
            start_sema_2.signal(thread_count);

            for(int t = 0; t < thread_count; ++t) {
                end_sema.wait();
            }
        }

        #ifdef PROFILE_SEMAPHORE
        compute_loop_profiler.stop();
        #endif

        auto stop = std::chrono::high_resolution_clock::now();
        results.push_back(chrono::duration_cast<std::chrono::microseconds>(stop - start).count());
        
        // ====================================================== //
        // Профайлинг семафоров //
        // ====================================================== //

        #ifdef PROFILE_SEMAPHORE
        double compute_loop_time_real = static_cast<double>(compute_loop_profiler.get_real_time()) / (1000 * RUN_COUNT);
        double compute_loop_time_sema = static_cast<double>(compute_loop_profiler.get_sema_time()) / (thread_count * 1000 * RUN_COUNT);

        printf("Работа с семафорами в главном цикле заняла %3.2lf% времени, а именно %3.2lfms из %3.2lfms\n",
            compute_loop_time_sema / compute_loop_time_real * 100,
            compute_loop_time_sema,
            compute_loop_time_real
        );
        #endif

        // ====================================================== //
        // Очистка //
        // ====================================================== //

        for(int t = 0; t < thread_count; ++t) {
            thread_pool[t] -> join();
            
            delete thread_pool[t];
        }
        
        for(auto sema_ptr: semaphores) {
            if(sema_ptr != nullptr) {
                delete sema_ptr;
            }
        }
    }
    else {
        // ====================================================== //
        // Простой случай //
        // ====================================================== //

        auto start = std::chrono::high_resolution_clock::now();

        single_thread_worker(lines, queue_size);

        auto stop = std::chrono::high_resolution_clock::now();
        results.push_back(chrono::duration_cast<std::chrono::microseconds>(stop - start).count());
    }

    for(auto line_ptr: lines) {
        delete line_ptr;
    }

    // ====================================================== //
    // Готово //
    // ====================================================== //

    return results;
}


int main(int argc, const char* argv[]) {
    vector<uint64_t> results;

    if(argc == 2) {
        results = main_routine(argv[1]);
    }
    else {
        results = main_routine(INPUT_PATH);
    }

    uint64_t sum = 0;
    for(int i = 0; i < results.size(); ++i) sum = sum + results[i];

    #ifdef IN_SCRIPT
    printf("%3.3lf\n", static_cast<double>(sum) / (RUN_COUNT * 1000));
    #else
    printf("Mean time: %3.3lfms\n", static_cast<double>(sum) / (RUN_COUNT * 1000));
    #endif

    return 0;
}