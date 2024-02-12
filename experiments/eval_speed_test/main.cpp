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

using namespace std;

const char input_path[] = "cut.txt";                    //См описание структуры Line
const int RUN_COUNT = 10;                               //Число запусков теста. Программа выводит среднее время работы теста в миллисекундах

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
    Line(const Line&) = delete;
};

void worker(vector<const Line*> lines,              //Весь "код" из cut.txt
            vector<const Semaphore*> Semaphores,    //Семафоры для синхронизиции потоков или nullptr если результат вершины используется только в ее потоке
            int thread,                       //Номер потока этого воркера
            Semaphore* start_sema_1,          //Два семафора, отвечающие за
            Semaphore* start_sema_2,          //  (почти) синхронный старт воркеров
            vector<int> queue_size) {         //Число вершин из отличного от thread потока, желающих получить доступ к текущей вершине

    auto line_queue = vector<const Line*>();              //Выделяем только те вершины, которые обрабатываются текущим потоком
    for(auto line_ptr: lines)  {
        if(line_ptr -> thread == thread) {
            line_queue.push_back(line_ptr);
        }
    }

    start_sema_1 -> signal();                       //Гарантия "одновременного" старта
    start_sema_2 -> wait();

    int queue_len = line_queue.size();
    for(int line_iter = 0; line_iter < queue_len; ++line_iter) {    //Большой кусок кода про последовалельную симуляцию работы вершин ТОЛЬКО текущего потока
        auto line_ptr = line_queue[line_iter];

        int len_dep = (line_ptr -> sync_deps).size();               //Обрабатываем зависимости между потоками
        for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
            int dep = (line_ptr -> sync_deps)[dep_iter];

            Semaphores[dep] -> wait();

            int data_pos = 0;
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

            int data_pos = 0;
            for(size_t i = 0; i < lines[dep] -> data.size(); ++i, ++data_pos) {
                if(data_pos >= line_ptr -> weight) {
                    data_pos = 0;
                }

                line_ptr -> data[data_pos] += lines[dep] -> data[i];
            }
        }

        int q = queue_size[line_ptr -> index];                      //Говорим всем, что мы посчитали свое значение и другим потокам можно его читать
        if(q > 0) {
            Semaphores[line_ptr -> index] -> signal(q);
        }
    }

    return;
}

int main_routine() {                                                        
    printf("Reading\n");                                            //Чтение из cut.txt

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

    printf("%lu lines read\n", lines.size());

    int max_thread = -1;                                                                    //Вычисляем реальное число потоков, т.к. gen.py может не использовать часть из них
    for(auto line_ptr: lines) {
        if(line_ptr -> thread > max_thread) max_thread = line_ptr -> thread;
    }
    int thread_count = max_thread + 1;

    printf("Thread count: %d\n", thread_count);                                             

    vector<int> queue_size(lines.size(), 0);                                                //Массив, определяющий число вешнин из других потоков, зависящих от данной
    for(auto line_ptr: lines) {
        for(auto dep: line_ptr -> sync_deps) {
                ++queue_size[dep];
        }
    }

    vector<long> results;                                                                   //Результаты тестирования в миллисекундах

    for(int run = 0; run < RUN_COUNT; ++run) {                                              //Основной цикл, см RUN_COUNT
        auto Semaphores = vector<const Semaphore*>();                                             //Семафоры или nullptr для синхронизации между потоками
        for(auto q: queue_size) {
            if(q > 0) {
                Semaphores.push_back(new Semaphore);
            }
            else {
                Semaphores.push_back(nullptr);
            }
        }

        vector<thread*> thread_pool(thread_count, nullptr);                                 
        Semaphore start_sema_1(thread_count);                                               //Семафоры для (почти) одновременного заппуска основной нагрузки потоков
        Semaphore start_sema_2(thread_count);                                               //  после выполнения их подготовки

        for(int t = 0; t < thread_count; ++t) {
            thread_pool[t] = new thread(worker, lines, Semaphores, t, &start_sema_1, &start_sema_2, queue_size);
        }

        for(int t = 0; t < thread_count; ++t) {
            start_sema_1.wait();
        }

        auto start = std::chrono::high_resolution_clock::now();
        
        for(int t = 0; t < thread_count; ++t) {
            start_sema_2.signal();
        }

        for(int t = 0; t < thread_count; ++t) {
            thread_pool[t] -> join();
        }

        auto stop = std::chrono::high_resolution_clock::now();

        results.push_back(chrono::duration_cast<std::chrono::milliseconds>(stop - start).count());

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

    #ifdef IN_SCRIPT
    printf( "result %3.1lf\n", static_cast<double>(sum) / RUN_COUNT);
    #else
    printf("Mean time: %3.1lfms\n", static_cast<double>(sum) / RUN_COUNT);
    #endif

    return 0;
}

int main() {
    return main_routine();
}