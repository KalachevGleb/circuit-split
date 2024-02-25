#ifndef WORKER_HPP
#define WORKER_HPP

#include <vector>
#include <string>
#include <algorithm>

#include "common.hpp"
#include "line.hpp"
#include "semaphore.hpp"

void pretty_worker(std::vector<const Line*> lines,                   //Весь "код" из cut.txt
                   std::vector<const Semaphore*> semaphores,         //Семафоры для синхронизиции потоков или nullptr если результат вершины используется только в ее потоке
                   int thread,                                       //Номер потока этого воркера
                   Semaphore* start_sema_1,                          //Семафоры, отвечающие за
                   Semaphore* start_sema_2,                          //  (почти) синхронный старт 
                   Semaphore* end_sema,                              //  и остановку воркеров
                   std::vector<int> queue_size);                     //Число вершин из отличного от thread потока, желающих получить доступ к текущей вершине

void single_thread_worker(std::vector<const Line*> lines,              //Весь "код" из cut.txt
                          std::vector<int> queue_size);

#endif