import json
import sys

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

def dummy_reorder(graph): 
    turn2vertex_id = np.full(len(graph.vs), dtype=int, fill_value=-1)
    buff = [vertex.index for vertex in graph.vs if vertex['w'] == 0]
    turn2vertex_id[:len(buff)] = np.array(buff, dtype=int)
    
    curr_thread = 0
    iter = len(buff)
    t2v_set = set(turn2vertex_id)

    pbar = tqdm(total=len(turn2vertex_id))
    while iter != len(graph.vs):

        for vertex in graph.vs:
            if vertex.index in t2v_set:
                continue

            if vertex['p'] != curr_thread:
                continue
            
            good = True
            for parent in vertex.neighbors(mode='in'):
                if parent.index not in t2v_set:
                    good = False
                    break

            if good:
                turn2vertex_id[iter] = vertex.index
                t2v_set.add(vertex.index)
                iter += 1
                pbar.update(1)
                break
                
        curr_thread = (curr_thread + 1) % THREAD_COUNT
    pbar.close()

    return turn2vertex_id.tolist()

def dummy_reorder2(graph): #WIP, doesn't work
    turn2vertex_id = np.full(len(graph.vs), dtype=int, fill_value=-1)
    buff = [vertex.index for vertex in graph.vs if vertex['w'] == 0]
    turn2vertex_id[:len(buff)] = np.array(buff, dtype=int)
    
    curr_thread = 0
    iter = len(buff)
    #unused_children = [set([vertex_id for vertex_id in turn2vertex_id[:len(buff)] if graph.vs[vertex_id]['p'] == thread]) for thread in range(THREAD_COUNT)]
    last_layer = set(buff)
    unused_children = [set()] * THREAD_COUNT

    pbar = tqdm(total=len(turn2vertex_id))
    while iter != len(graph.vs):

        found = False
        for vertex_id in unused_children[curr_thread].copy():
            vertex = graph.vs[vertex_id]

            if vertex['p'] != curr_thread:
                continue
            
            turn2vertex_id[iter] = vertex_id
            iter += 1

            unused_children[curr_thread].remove(vertex_id)
            last_layer.add(vertex_id)

            for parent in vertex.neighbors(mode='in'):

                has_child = False
                for child in parent.neighbors(mode='out'):

                    if child.index in set.union(*unused_children):
                        has_child = True
                        break

                if not has_child:
                    last_layer.remove(parent.index)

            found = True
            pbar.update(1)
            break

        if not found:
            unused_children = [set()] * THREAD_COUNT

            last_layer_set = set(last_layer)    
            for vertex_id in last_layer_set:
                for child in graph.vs[vertex_id].neighbors(mode='out'):

                    # if child.index in last_layer_set:
                    #     continue

                    parents = [parent.index for parent in child.neighbors(mode='in')]

                    if set(parents).issubset(last_layer_set):
                        unused_children[child['p']].add(child.index)

        curr_thread = (curr_thread + 1) % THREAD_COUNT
    pbar.close()

    return turn2vertex_id.tolist()                
    
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
        cost_greedy = cut_graph(graph=graph, turn2vertex_id=turn2vertex_id)
        for i in range(15):
            print('Стоимость:', np.amax(cost_greedy))
            turn2vertex_id = dummy_reorder(graph)
            cost_greedy = cut_graph(graph=graph, turn2vertex_id=turn2vertex_id)
    elif MODE == 4:
        best_cost = 10 ** 10
        for i in tqdm_friendly(range(100)):
            graph.vs['p'] = np.random.choice([i for i in range(THREAD_COUNT)], nc, p=[1. / THREAD_COUNT] * THREAD_COUNT)
            cost_greedy = cut_graph(graph=graph, turn2vertex_id=turn2vertex_id)
            best_cost = min(best_cost, np.amax(cost_greedy))

    print_freindly('Стоимость:', cost_greedy)
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