#include "worker.hpp"
#include "defines.hpp"
#include "semaphore.hpp"

using namespace std;

void pretty_worker(std::vector<const Line*> lines,                   //Весь "код" из cut.txt
                   std::vector<const Semaphore*> semaphores,         //Семафоры для синхронизиции потоков или nullptr если результат вершины используется только в ее потоке
                   int thread,                                       //Номер потока этого воркера
                   Semaphore* start_sema_1,                          //Семафоры, отвечающие за
                   Semaphore* start_sema_2,                          //  (почти) синхронный старт 
                   Semaphore* end_sema,                              //  и остановку воркеров
                   std::vector<int> queue_size) {                    //Число вершин из отличного от thread потока, желающих получить доступ к текущей вершине
                   
    auto line_queue = vector<const Line*>();              //Выделяем только те вершины, которые обрабатываются текущим потоком
    for(auto line_ptr: lines)  {
        if(line_ptr -> thread == thread) {
            line_queue.push_back(line_ptr);
        } 
    }

    #ifdef PROFILE
    auto start = std::chrono::high_resolution_clock::now();
    #endif

    for(int worker_iteration = 0; worker_iteration < RUN_COUNT; ++worker_iteration) {
        start_sema_1 -> signal();                       //Гарантия "одновременного" старта
        start_sema_2 -> wait();

        for(int line_iter = 0; line_iter < line_queue.size(); ++line_iter) {    //Большой кусок кода про последовалельную симуляцию работы вершин ТОЛЬКО текущего потока
            auto line_ptr = line_queue[line_iter];

            #ifdef DEBUG_PRINT
            if(thread == DEBUG_THREAD) {
                printf("%d", line_ptr -> index);
            }
            #endif

            int len_dep = (line_ptr -> sync_deps).size();               //Обрабатываем зависимости между потоками
            for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
                int dep = (line_ptr -> sync_deps)[dep_iter];

                semaphores[dep] -> wait();

                #ifdef DEBUG_PRINT
                if(thread == DEBUG_THREAD) {
                    printf(" %d", -dep -1);
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

    #ifdef PROFILE
    auto stop = std::chrono::high_resolution_clock::now();
    if(thread == DEBUG_THREAD) {
        printf("Поток %d считался %3.2lfms\n", thread, static_cast<double>(chrono::duration_cast<std::chrono::microseconds>(stop - start).count()) / (1000 * RUN_COUNT));
    }
    #endif

    return;
}

void single_thread_worker(vector<const Line*> lines,              //Весь "код" из cut.txt
                          vector<int> queue_size) {         //Число вершин из отличного от thread потока, желающих получить доступ к текущей вершине

    for(int worker_iteration = 0; worker_iteration < RUN_COUNT; ++worker_iteration) {
        
        int queue_len = lines.size();
        for(int line_iter = 0; line_iter < queue_len; ++line_iter) {    //Большой кусок кода про последовалельную симуляцию работы вершин ТОЛЬКО текущего потока
            auto line_ptr = lines[line_iter];

            #ifdef DEBUG_PRINT
            printf("%d", line_ptr -> index);
            #endif
            
            int len_dep = (line_ptr -> forward_deps).size();                //Обрабатываем зависимости внутри потока
            for(int dep_iter = 0; dep_iter < len_dep; ++dep_iter) {
                int dep = (line_ptr -> forward_deps)[dep_iter];
                
                #ifdef DEBUG_PRINT
                printf(" %d", dep);
                #endif

                int data_pos = 0;
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