import json
import sys

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

IN_SCRIPT = False
FRIENDLY = True
MODE = 2

THREAD_COUNT = int(sys.argv[1])
LOSS = float(sys.argv[2])
LOSS2 = float(sys.argv[3])

# TODO
# Комментарии

filename = 'blob/dep_graph.json'

def print_freindly(*args):
    if FRIENDLY:
        print(*args)

def print_in_script(*args):
    if IN_SCRIPT:
        print(*args)

def tqdm_friendly(args):
    if FRIENDLY:
        return tqdm(args)
    else:
        return args
    
def cut_graph(graph, turn2vertex_id):
    time_per_thread = [0] * THREAD_COUNT

    for vertex_id in tqdm_friendly(turn2vertex_id):

        vertex = graph.vs[vertex_id]
        parents = vertex.neighbors(mode='in')

        if len(parents) == 0:
            vertex['t'] = 0
            vertex['p'] = 0
            continue

        proposed_time_per_thread = [None] * THREAD_COUNT
        for thread in range(THREAD_COUNT):
            t = time_per_thread[thread]
            for parent in parents:
                if parent['p'] != thread:
                    t += parent['w'] * LOSS + LOSS2
                else:
                    t += parent['w']

            proposed_time_per_thread[thread] = t

        thread = np.argmin(proposed_time_per_thread)

        time_per_thread[thread] = proposed_time_per_thread[thread]
        
        vertex['p'] = thread
        vertex['t'] = proposed_time_per_thread[thread]

    cost_greedy = time_per_thread

    return cost_greedy

def possible_steps(graph, turn2vertex_id):
    pass


def reorder(graph):
    semaphores = [edge for edge in graph.es if edge[0]['p'] != edge[1]['p']]

    turn2vertex_id = []

    for vertex in graph.vs:
        parents = vertex.neighbors(mode='in')

        good = True
        for parent in parents:
            if parent.index not in turn2vertex_id:
                good = False

                break
        
        if good:
            turn2vertex_id.append(parent.index)
        



def main():
    if len(sys.argv) not in [4, 5]:
        print_freindly('Ожидались желаемое число потоков, стоимость мьютекса[, и путь до выходного файла]')
        quit(1)

    print_freindly('Чтение графа')

    fd = open(filename, 'r')
    graph_raw = json.load(fd)
    fd.close()

    nc = len(graph_raw['node_weights'])
    ec = len(graph_raw['edges'])

    graph_raw['edges'] = [(e[1], e[0]) for e in graph_raw['edges']]    

    graph = ig.Graph(nc, directed=True)
    graph.vs['w'] = graph_raw['node_weights']
    graph.add_edges(graph_raw['edges'])

    turn2vertex_id = graph.topological_sorting(mode='out')

    if MODE == 1:
        single_thread_time = np.sum(graph.vs['w'])
    if MODE == 2:
        single_thread_time = np.sum(np.array(graph.vs['w'], dtype=np.int64) * np.array([len(vertex.neighbors(mode='out')) for vertex in graph.vs], dtype=np.int64))

    print_freindly('Стоимость однопоточного вычисления:', single_thread_time)

    print_freindly('Использую жадный алгоритм')
    
    print_freindly('Гафи интерпретируется в режиме', MODE)

    if MODE == 1:
        time_per_thread = [0] * THREAD_COUNT

        for vertex_id in tqdm_friendly(turn2vertex_id):

            vertex = graph.vs[vertex_id]
            parents = vertex.neighbors(mode='in')

            if vertex['w'] == 0:
                vertex['t'] = 0
                vertex['p'] = 0
                continue

            proposed_time_per_thread = [None] * THREAD_COUNT
            for thread in range(THREAD_COUNT):
                t = -1
                for parent in parents:
                    if parent['p'] != thread:
                        t = max(vertex['w'] + parent['t'] + LOSS, t)
                    else:
                        t = max(vertex['w'] + parent['t'], t)

                if t < time_per_thread[thread] + vertex['w']:
                    t = time_per_thread[thread] + vertex['w']

                proposed_time_per_thread[thread] = t

            thread = np.argmin(proposed_time_per_thread)

            time_per_thread[thread] = proposed_time_per_thread[thread]
            
            vertex['p'] = thread
            vertex['t'] = proposed_time_per_thread[thread]

        cost_greedy = time_per_thread
    elif MODE == 2:
        cost_greedy = cut_graph(graph=graph, turn2vertex_id=turn2vertex_id)
    elif MODE == 3:
        pass

    print_freindly('Стоимость потоков:', cost_greedy)
    print_freindly('Overhead:', str(sum(cost_greedy) - np.sum(graph.vs['w'])))
    print_freindly('Выгода: ' + str(round(100 * (1 - max(cost_greedy) / single_thread_time), 3)) + '%')

    if IN_SCRIPT:
        print_in_script(max(cost_greedy))

    print_freindly('Делаю дамп разреза')                                                  
    
    fd = open('cut.txt', 'w')                                                   #См структуру Line в main.cpp

    vertex_id2turn = [None for _ in range(len(turn2vertex_id))]                 #Строим отображение id вершны в ее место по очереди в топологической сортировке
    for i in range(len(turn2vertex_id)):                                        #   то есть обратное к turn2vertex_id
        vertex_id2turn[turn2vertex_id[i]] = i

    cross_thread_copies = 0
    for vertex_id in turn2vertex_id: #tqdm(turn2vertex_id):                                      #Последовательно дампим расписание в cut.txt в соотвествии с правилом, описанным
                                                                                #   в комментарии к структуре Line в main.cpp
        vertex = graph.vs[vertex_id]
        parents = vertex.neighbors(mode='in')

        fd.write(str(vertex['p']))
        fd.write(' ')
        fd.write(str(vertex_id2turn[vertex_id]))
        fd.write(' ')
        fd.write(str(vertex['w']))

        for parent in parents:
           
            fd.write(' ')

            if parent['p'] != vertex['p']:
                fd.write(str(-vertex_id2turn[parent.index] - 1))
                
                cross_thread_copies += 1
            else:
                fd.write(str(vertex_id2turn[parent.index]))

        fd.write('\n')

    fd.close()

    print_freindly('Передач между потоками:', cross_thread_copies)

    print_freindly('Готово! Have a nice day :)')

if __name__ == '__main__':
    main()