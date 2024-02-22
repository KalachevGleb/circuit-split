import json
import sys

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

# TODO
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

filename = 'blob/CONTAINER_SET_8_0_1.json' #'blob/dep_graph.json'

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
    turn2vertex_id = [vertex.index for vertex in graph.vs if len(vertex.neighbors(mode='in')) == 0]
    
    t2v_id_size_iter = len(turn2vertex_id)
    turn2vertex_id += [-1] * (len(graph.vs) - t2v_id_size_iter)
    turn2vertex_id = np.array(turn2vertex_id, dtype=int)

    time_per_thread = [0] * THREAD_COUNT

    pbar = tqdm(total=len(turn2vertex_id))
    while t2v_id_size_iter != len(graph.vs):

        #print(t2v_id_size_iter, 'of', len(graph.vs))
        
        previous_t2v_id_size_iter = t2v_id_size_iter
        while True:
            improved = False
            for vertex_id in turn2vertex_id[:t2v_id_size_iter]:

                vertex = graph.vs[vertex_id]
                children = vertex.neighbors(mode='out')

                for child in children:
                    if child.index in turn2vertex_id[:t2v_id_size_iter]:
                        continue

                    parents = child.neighbors(mode='in')
                    
                    good = True
                    for parent in parents:
                        #if parent['p'] != child['p']:
                        if parent['p'] != child['p'] or (parent.index not in turn2vertex_id[:previous_t2v_id_size_iter]): ###!!!!!!!!!!!!!!!!!!!
                            good = False

                            break
                    
                    if good:
                        turn2vertex_id[t2v_id_size_iter] = child.index
                        t2v_id_size_iter += 1
                        
                        improved = True
            #print(1)
            if not improved:
                break






        added = turn2vertex_id[previous_t2v_id_size_iter:t2v_id_size_iter]

        costs = [0] * THREAD_COUNT
        for vertex_id in added:
            vertex = graph.vs[vertex_id]

            thread = vertex['p']
            
            for parent in vertex.neighbors(mode='in'):
                if thread == parent['p']:
                    costs[thread] += parent['w']
                else:
                    costs[thread] += LOSS * parent['w'] + LOSS2






        goal = np.amin(costs)

        skip_costs = [0] * THREAD_COUNT
        not_skipped = []
        for vertex_id in added:
            vertex = graph.vs[vertex_id]

            thread = vertex['p']
            if skip_costs[thread] > goal:
                continue
            
            not_skipped.append(vertex_id)
            
            for parent in vertex.neighbors(mode='in'):
                if thread == parent['p']:
                    skip_costs[thread] += parent['w']
                else:
                    skip_costs[thread] += LOSS * parent['w'] + LOSS2











        turn2vertex_id[previous_t2v_id_size_iter:previous_t2v_id_size_iter + len(not_skipped)] = not_skipped
        t2v_id_size_iter = previous_t2v_id_size_iter + len(not_skipped)

        




        for vertex_id in turn2vertex_id[:t2v_id_size_iter]:
            vertex = graph.vs[vertex_id]

            children = vertex.neighbors(mode='out')

            for child in children:
                if child['p'] == vertex['p']:
                    continue

                if child.index not in turn2vertex_id[:t2v_id_size_iter]:
                    turn2vertex_id[t2v_id_size_iter] = child.index
                    t2v_id_size_iter += 1

        pbar.update(t2v_id_size_iter - previous_t2v_id_size_iter)

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
    if MODE in [2, 3]:
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
        cost_greedy = cut_graph(graph=graph, turn2vertex_id=turn2vertex_id)
        for i in range(15):
            print('Стоимость:', np.amax(cost_greedy))
            turn2vertex_id = reorder(graph)
            cost_greedy = cut_graph(graph=graph, turn2vertex_id=turn2vertex_id)

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