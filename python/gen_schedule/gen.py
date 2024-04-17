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
# Симулировать точки синхронизации в жадном алгоритме в общем виде - не только один поток ждет набор других
# Оптимизировать точки синхронизации после их генерации
# Добавить проверку на порядок

FRIENDLY = True
TQDM_FRIENDLY = True
MODE = 3
MODE2_ITER = 1000

THREAD_COUNT = None
LOSS1 = None
LOSS2 = None

def print_freindly(*args):
    if FRIENDLY:
        print(*args)

def tqdm_friendly(args):
    if TQDM_FRIENDLY:
        return tqdm(args)
    else:
        return args

def cut_graph_greedy(graph, turn2vertex_id):
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
                    t += parent['w'] * LOSS1 + LOSS2
                else:
                    t += parent['w']

            proposed_time_per_thread[thread] = t

        thread = np.argmin(proposed_time_per_thread)

        time_per_thread[thread] = proposed_time_per_thread[thread]
        
        vertex['p'] = thread
        vertex['t'] = proposed_time_per_thread[thread]

    cost_greedy = time_per_thread

    return cost_greedy

def cut_graph_depth(graph):
    layers = [set([vertex.index for vertex in graph.vs if vertex.neighbors(mode='in') == []])]

    previously_used_vertices = layers[0].copy()
    ready_size = len(layers[0])
    while ready_size != len(graph.vs): 
        rejected = set()
        new_layer = set()

        for vertex_id in layers[-1]:
            vertex = graph.vs[vertex_id]

            for child in vertex.neighbors(mode='out'):
                child_id = child.index

                if child_id in rejected:
                    continue
                if child_id in new_layer:
                    continue
                if child_id in previously_used_vertices:
                    continue
                
                good = True
                for parent in child.neighbors(mode='in'):
                    if parent.index not in previously_used_vertices:
                        good = False
                        break

                if good:
                    new_layer.add(child_id)
                else:
                    rejected.add(child_id)

        layers.append(new_layer)

        previously_used_vertices.update(new_layer)
        ready_size += len(new_layer)

    layers = [sorted(list(layer)) for layer in layers]

    for vertex_id in layers[0]:
        graph.vs[vertex_id]['p'] = 0

    heavinesses = []
    pbar = tqdm(total=len(graph.vs))
    for layer in layers[1:]:
        heavinesses.append(np.zeros(shape=(THREAD_COUNT,)))

        for i in range(len(layer)):
            vertex_id = layer[i]
            vertex = graph.vs[vertex_id]

            thread = int(i / len(layer) * THREAD_COUNT)
            graph.vs[vertex_id]['p'] = thread

            heavinesses[-1][thread] += sum(parent['w'] for parent in vertex.neighbors(mode='in'))

        pbar.update(len(layer))
    pbar.close()

    return layers, heavinesses

def reorder_graph(graph): 
    turn2vertex_id = [vertex.index for vertex in graph.vs if vertex['w'] == 0]
    t2v_id_set = set(turn2vertex_id)

    mem = [deque() for _ in range(THREAD_COUNT)]
    mem_set = set()
    for vertex_id in turn2vertex_id:
        vertex = graph.vs[vertex_id]

        for child in vertex.neighbors(mode='out'):
            good = True

            for parent in child.neighbors(mode='in'):
                if parent.index not in t2v_id_set:
                    good = False
                    break

            if good and child.index not in mem_set:
                mem[child['p']].append(child.index)
                mem_set.add(child.index)

    curr_thread = 0
    pbar = tqdm(total=len(turn2vertex_id))
    while len(turn2vertex_id) != len(graph.vs):
        if len(mem[curr_thread]) == 0:
            curr_thread += 1
            curr_thread %= THREAD_COUNT
            continue

        vertex_id = mem[curr_thread].popleft()
        mem_set.remove(vertex_id)
        vertex = graph.vs[vertex_id]

        turn2vertex_id.append(vertex_id)
        t2v_id_set.add(vertex_id)

        for child in vertex.neighbors(mode='out'):
            good = True

            for parent in child.neighbors(mode='in'):
                if parent.index not in t2v_id_set:
                    good = False
                    break

            if good and child.index not in mem_set:
                mem[child['p']].append(child.index)
                mem_set.add(child.index)

        curr_thread += 1
        curr_thread %= THREAD_COUNT
        
        pbar.update(1)
    pbar.close()

    return turn2vertex_id     
    
def main():
    print_freindly('Чтение графа')

    with open(IN_PATH, 'r') as fd:
        graph_raw = json.load(fd)
        if 'graph' in graph_raw.keys():
            graph_raw = graph_raw['graph']

    nc = len(graph_raw['node_weights'])
    ec = len(graph_raw['edges'])

    graph_raw['edges'] = [(e[1], e[0]) for e in graph_raw['edges']]    

    graph = ig.Graph(nc, directed=True)
    graph.vs['w'] = graph_raw['node_weights']
    graph.add_edges(graph_raw['edges'])

    print_freindly('Прочитан граф на', len(graph.vs), 'вершин')

    turn2vertex_id = graph.topological_sorting(mode='out')

    if MODE in list(range(1000)):
        single_thread_time = np.sum(np.array(graph.vs['w'], dtype=np.int64) * np.array([len(vertex.neighbors(mode='out')) for vertex in graph.vs], dtype=np.int64))

    print_freindly('Стоимость однопоточного вычисления:', single_thread_time)
    print_freindly('Граф интерпретируется в режиме', MODE)

    #
    #
    # Генерация расписания
    #
    #

    if MODE == 1:
        heaviness = cut_graph_greedy(graph=graph, turn2vertex_id=turn2vertex_id)

        memory_order = list(range(len(graph.vs)))

        cost = np.amax(heaviness)
    elif MODE == 2:
        old_t2v_id = []
        for i in tqdm_friendly(range(MODE2_ITER)):
            heaviness = cut_graph_greedy(graph=graph, turn2vertex_id=turn2vertex_id)
            turn2vertex_id = reorder_graph(graph=graph)
            
            h = hash(str(turn2vertex_id))
            if h in old_t2v_id:
                break
            old_t2v_id.append(h)

        memory_order = list(range(len(graph.vs)))

        cost = np.amax(heaviness)
    elif MODE == 3:
        layers, heavinesses = cut_graph_depth(graph=graph)

        memory_order = sum(layers, [])
    else:
        print_freindly('Неизвестный MODE:', MODE)
        quit(1)

    #
    #
    # Проверка расписания
    #
    #

    print_freindly('Проверяю расписание')
    if MODE in [1, 2]:
        if len(turn2vertex_id) != len(set(turn2vertex_id)):
            print_freindly('В построенном расписании есть повторяющиеся вершины')
            quit(2)
        if np.amax(turn2vertex_id) != nc - 1 or np.amin(turn2vertex_id) != 0:
            print_freindly('В построенном расписании есть номера вершин, которых нет в графе')
            quit(2)
        print_freindly('TODO: Добавить полную проверку корректности расписания')
        print_freindly('OK')
    elif MODE == 3:
        print_freindly('Не умею проверять расписание для MODE == 3')
    else:
        print_freindly('Неизвестный MODE:', MODE)
        quit(1)

    #
    #
    # Метрики
    #
    #
    
    if MODE in [1, 2]:
        print_freindly('Стоимость:', heaviness)
        print_freindly('Overhead:', str(sum(heaviness) - single_thread_time))
        print_freindly('Выгода: ' + str(round(100 * (single_thread_time - cost) / single_thread_time, 3)) + '%')
    elif MODE == 3:
        print_freindly('Барьеров:', len(layers))
        print_freindly('Утилизация потоков:',
                       str(round(float(
                             np.sum([np.sum(h) for h in heavinesses]) /
                             np.sum([np.amax(h) * THREAD_COUNT for h in heavinesses]) *
                             100
                       ), 3)) + '%')
    else:
        print_freindly('Неизвестный MODE:', MODE)
        quit(1)

    #
    #
    # Перевод в json
    #
    #

    print_freindly('Преобразую расписание к стандартному виду')

    if MODE in [1, 2]:
        schedule = [[] for _ in range(THREAD_COUNT)]
        sync_points = []
        for vertex_id in turn2vertex_id:
            vertex = graph.vs[vertex_id]
            curr_thread = int(vertex['p'])

            A = [curr_thread]
            parents = vertex.neighbors(mode='in')
            B = sorted(list(set([int(parent['p']) for parent in parents if parent['p'] != curr_thread])))

            if B != []: #Есть родители из соседних потоков
                sync_points.append([A, B])

                for thread in set(map(int, A + B)):
                    schedule[thread].append([1, len(sync_points) - 1])
            
            schedule[curr_thread].append([0, int(vertex_id)])
    elif MODE == 3:
        schedule = [[] for _ in range(THREAD_COUNT)]
        sync_points = []

        for layer in layers:
            for vertex_id in layer:
                vertex = graph.vs[vertex_id]
                curr_thread = int(vertex['p'])

                schedule[curr_thread].append([0, vertex_id])

            for thread in range(THREAD_COUNT):
                schedule[thread].append([1, len(sync_points)])

            sync_points.append([list(range(THREAD_COUNT)), list(range(THREAD_COUNT))])
    else:
        print_freindly('Неизвестный MODE:', MODE)
        quit(1)

    #
    #
    # Дамп
    #
    #

    print_freindly('Запись в json')

    graph_raw['edges'] = [(e[1], e[0]) for e in graph_raw['edges']] 
    with open(OUT_PATH, 'w') as fd:
        print(OUT_PATH)
        json.dump({
            'graph' : graph_raw,
            'memory_order' : memory_order,
            'schedule' : schedule,
            'sync_points' : sync_points
        }, fd, indent=4)

    print_freindly('Синхронизаций:', len(sync_points))

    #
    #
    #
    #
    #

    print_freindly('Готово! Have a nice day :)')

if __name__ == '__main__':#
    if len(sys.argv) not in [4, 5, 6]:
        print_freindly('Ожидались желаемое число потоков, пареметры стоимости мьютекса[, и путь до выходного файла]')
        quit(1)

    THREAD_COUNT = int(sys.argv[1])
    LOSS1 = float(sys.argv[2])
    LOSS2 = float(sys.argv[3])
    IN_PATH = '50k.json'
    OUT_PATH = 'cut.json'
    if len(sys.argv) >= 5:
        IN_PATH = sys.argv[4]
    if len(sys.argv) >= 6:
        OUT_PATH = sys.argv[5]

    if THREAD_COUNT == 1:
        MODE = 1

    main()