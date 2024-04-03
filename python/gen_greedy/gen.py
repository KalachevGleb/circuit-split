import json
import sys
from collections import deque

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

# TODO
# За кождый поток делать по шагу
# Действительно поптимальный reorder()
# Перестановка алгоритмов
# Модули в схеме - группировка под кэши
# ML

IN_SCRIPT = False
FRIENDLY = True
MODE = 3

THREAD_COUNT = int(sys.argv[1])
LOSS = float(sys.argv[2])
LOSS2 = float(sys.argv[3])

# TODO
# Комментарии

filename = 'blob/CONTAINER_SET_8_0_1.json' 

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

def reorder_graph(graph): 
    turn2vertex_id = [vertex.index for vertex in graph.vs if vertex['w'] == 0]
    t2v_id_set = set(turn2vertex_id)

    mem = [deque() for _ in range(THREAD_COUNT)]
    for vertex_id in turn2vertex_id.copy():
        vertex = graph.vs[vertex_id]

        for child in vertex.neighobors(mode='out'):
            good = True

            for parent in child.neighbors(mode='in'):
                if parent.index not in t2v_id_set:
                    good = False
                    break

            if good:
                mem[child['t']].append(child.index)

    curr_thread = 0
    pbar = tqdm(total=len(turn2vertex_id))
    while len(turn2vertex_id) != len(graph.vs):
        if len(mem[curr_thread]) == 0:
            curr_thread += 1
            curr_thread %= THREAD_COUNT
            continue

        vertex_id = mem[curr_thread].popleft()
        vertex = graph.vs[vertex_id]

        turn2vertex_id.append(vertex_id)
        t2v_id_set.add(vertex_id)

        for child in vertex.neighbors(mode='out'):
            good = True

            for parent in child.neighbors(mode='in'):
                if parent.index not in t2v_id_set:
                    good = False
                    break

            if good:
                mem[child['t']].append(child.index)

        curr_thread += 1
        curr_thread %= THREAD_COUNT
        
        pbar.update(1)
    pbar.close()

    return turn2vertex_id.tolist()           
    
def main():
    if len(sys.argv) != 4:
        print_freindly('Ожидались желаемое число потоков, пареметры стоимости мьютекса[, и путь до выходного файла]')
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

    print_freindly('Прочитан граф на', len(graph.vs), 'вершин')

    turn2vertex_id = graph.topological_sorting(mode='out')

    if MODE == 1:
        single_thread_time = np.sum(graph.vs['w'])
    if MODE in [2, 3, 4]:
        single_thread_time = np.sum(np.array(graph.vs['w'], dtype=np.int64) * np.array([len(vertex.neighbors(mode='out')) for vertex in graph.vs], dtype=np.int64))

    print_freindly('Стоимость однопоточного вычисления:', single_thread_time)
    print_freindly('Использую жадный алгоритм')
    print_freindly('Графы интерпретируется в режиме', MODE)

    if MODE == 1:
        cost_greedy = cut_graph(graph=graph, turn2vertex_id=turn2vertex_id)
        memory_order = list(range(len(graph.vs)))

    print_freindly('Стоимость:', cost_greedy)
    print_freindly('Overhead:', str(sum(cost_greedy) - np.sum(graph.vs['w'])))
    print_freindly('Выгода: ' + str(round(100 * (1 - max(cost_greedy) / single_thread_time), 3)) + '%')

    print_freindly('Делаю дамп разреза')

    with open('cut.json', 'w') as fd:
        json.dump({
            'graph' : graph_raw,
            'memory_order' : memory_order,
            'schedule' : [[[0, vertex_id] for vertex_id in schedule]],
            'sync_points' : []
        }, fd)

    print_freindly('Передач между потоками:', cross_thread_copies)

    print_freindly('Готово! Have a nice day :)')

if __name__ == '__main__':
    main()