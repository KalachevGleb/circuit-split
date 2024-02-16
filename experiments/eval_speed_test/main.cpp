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

#define DEBUG_THREAD 2

using namespace std;

const char INPUT_PATH[] = "cut.txt";                    //См описание структуры Line
const int RUN_COUNT = 50;                               //Число запусков теста. Программа выводит среднее время работы теста в миллисекундах

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

struct Line {
    int thread;
    int index;
    int weight;
    mutable vector<uint32_t> data;
    vector<int> forward_deps, sync_deps;            //Родители из текущего потока и родители из другого потока соответственно

    // Конструктор из строки cut.txt
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

        data.resize(max(1, weight));
    }

private:
    Line() = delete;
};

void worker(vector<const Line*> lines,              //Весь "код" из cut.txt
            vector<const Semaphore*> semaphores,    //Семафоры для синхронизиции потоков или nullptr если результат вершины используется только в ее потоке
            int thread,                       //Номер потока этого воркера
            Semaphore* start_sema_1,          //Два семафора, отвечающие за
            Semaphore* start_sema_2,          //  (почти) синхронный старт воркеров
            Semaphore* end_sema,
            vector<int> queue_size) {         //Число вершин из отличного от thread потока, желающих получить доступ к текущей вершине

    auto line_queue = vector<const Line*>();              //Выделяем только те вершины, которые обрабатываются текущим потоком
    for(auto line_ptr: lines)  {
        if(line_ptr -> thread == thread) {
            line_queue.push_back(line_ptr);
        } 
    }

    for(int worker_iteration = 0; worker_iteration < RUN_COUNT; ++worker_iteration) {
        start_sema_1 -> signal();                       //Гарантия "одновременного" старта
        start_sema_2 -> wait();

        for(int line_iter = 0; line_iter < line_queue.size(); ++line_iter) {    //Большой кусок кода про последовалельную симуляцию работы вершин ТОЛЬКО текущего потока
            volatile auto line_ptr = line_queue[line_iter];

            #ifdef DEBUG_PRINT
            if(thread == DEBUG_THREAD) {
                printf("%d", line_ptr -> index);
            }
            #endif

            volatile int len_dep = (line_ptr -> sync_deps).size();               //Обрабатываем зависимости между потоками
            for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
                int dep = (line_ptr -> sync_deps)[dep_iter];

                semaphores[dep] -> wait();

                #ifdef DEBUG_PRINT
                if(thread == DEBUG_THREAD) {
                    printf(" %d", -dep -1);
                }
                #endif

                volatile int data_pos = 0;
                for(size_t i = 0; i < lines[dep] -> data.size(); ++i, ++data_pos) {
                    if(data_pos >= line_ptr -> weight) {
                        data_pos = 0;
                    }

                    line_ptr -> data[data_pos] += lines[dep] -> data[i];
                }
            }
            
            len_dep = (line_ptr -> forward_deps).size();                //Обрабатываем зависимости внутри потока
            for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
                int dep = (line_ptr -> forward_deps)[dep_iter];

                #ifdef DEBUG_PRINT
                if(thread == DEBUG_THREAD) {
                    printf(" %d", dep);
                }
                #endif

                int data_pos = 0;
                for(size_t i = 0; i < lines[dep] -> data.size(); ++i, ++data_pos) {
                    if(data_pos >= line_ptr -> weight) {
                        data_pos = 0;
                    }

                    line_ptr -> data[data_pos] += lines[dep] -> data[i];
                }
            }

            int q = queue_size[line_ptr -> index];
            #ifdef DEBUG_PRINT
            if(thread == DEBUG_THREAD) {
                printf(" %d\n", q);
            }
            #endif                   
            if(q > 0) {
                semaphores[line_ptr -> index] -> signal(q);
            }
        }

        end_sema -> signal();
    }

    return;
}

void single_thread_worker(vector<const Line*> lines,              //Весь "код" из cut.txt
                          vector<int> queue_size) {         //Число вершин из отличного от thread потока, желающих получить доступ к текущей вершине

    for(int worker_iteration = 0; worker_iteration < RUN_COUNT; ++worker_iteration) {
        
        int queue_len = lines.size();
        for(int line_iter = 0; line_iter < queue_len; ++line_iter) {    //Большой кусок кода про последовалельную симуляцию работы вершин ТОЛЬКО текущего потока
            volatile auto line_ptr = lines[line_iter];

            #ifdef DEBUG_PRINT
            printf("%d", line_ptr -> index);
            #endif
            
            int len_dep = (line_ptr -> forward_deps).size();                //Обрабатываем зависимости внутри потока
            for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
                volatile int dep = (line_ptr -> forward_deps)[dep_iter];
                
                #ifdef DEBUG_PRINT
                printf(" %d", dep);
                #endif

                volatile int data_pos = 0;
                for(size_t i = 0; i < lines[dep] -> data.size(); ++i, ++data_pos) {
                    if(data_pos >= line_ptr -> weight) {
                        data_pos = 0;
                    }

                    line_ptr -> data[data_pos] += lines[dep] -> data[i];
                }
            }

            #ifdef DEBUG_PRINT
            printf("\n");
            #endif
        }
    }

    return;
}

vector<long> main_routine(const char* input_path) {    
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

    vector<long> results;
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
            thread_pool[t] = new thread(worker, lines, semaphores, t, &start_sema_1, &start_sema_2, &end_sema, queue_size);
        }

        // ====================================================== //
        // Прогон в цикле //
        // ====================================================== //

        for(int run = 0; run < RUN_COUNT; ++run) {
            for(int t = 0; t < thread_count; ++t) {
                start_sema_1.wait();
            }

            auto start = std::chrono::high_resolution_clock::now();
            
            start_sema_2.signal(thread_count);

            for(int t = 0; t < thread_count; ++t) {
                end_sema.wait();
            }

            auto stop = std::chrono::high_resolution_clock::now();

            results.push_back(chrono::duration_cast<std::chrono::milliseconds>(stop - start).count());
        }

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

        results.push_back(chrono::duration_cast<std::chrono::milliseconds>(stop - start).count());
    }

    for(auto line_ptr: lines) {
        delete line_ptr;
    }

    return results;
}

vector<Line> read_lines(const char* input_path) {
    ifstream fd;
    fd.open(input_path, ios_base::in);

    string read_buff;
    vector<Line> lines;
    if (fd.is_open()) {
        while (fd) {
            getline(fd, read_buff);

            if(split_string(read_buff).size() == 0) continue;       

            lines.push_back(Line(read_buff));
        }
    }

    fd.close();

    return lines;
}

vector<Line> schedule2lines(vector<int> schedule, vector<Line> clear_lines) {
    // TBD

    // auto ret = vector<Line>();

    // for(auto line_num: schedule) {
    //     Line result_line = clear_lines[line_num];

    //     int thread = schedule[]
    // }

    return vector<Line>();
}

int main(int argc, const char* argv[]) {
    vector<long> results;

    if(argc == 2) {
        results = main_routine(argv[1]);
    }
    else {
        results = main_routine(INPUT_PATH);
    }

    long sum = 0;
    for(int i = 0; i < results.size(); ++i) sum = sum + results[i];

    #ifdef IN_SCRIPT
    printf("%3.3lf\n", static_cast<double>(sum) / RUN_COUNT);
    #else
    printf("Mean time: %3.3lfms\n", static_cast<double>(sum) / RUN_COUNT);
    #endif

    return 0;
}