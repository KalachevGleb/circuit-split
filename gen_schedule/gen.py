import json
from collections import deque
import argparse
import os

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

import cpp
Cache = cpp.Cache
Layer = cpp.Layer

# TODO
# За кождый поток делать по шагу
# Действительно поптимальный reorder()
# Перестановка алгоритмов
# Модули в схеме - группировка под кэши
# ML
# Симулировать точки синхронизации в жадном алгоритме в общем виде - не только один поток ждет набор других
# Оптимизировать точки синхронизации после их генерации
# Добавить проверку на порядок

def print_freindly(*args):
    if MODE == 4:
        return
    
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

def cut_graph_random(graph, turn2vertex_id):
    for vertex_id in tqdm_friendly(turn2vertex_id):
        graph.vs[vertex_id]['p'] = np.random.randint(0, THREAD_COUNT)

    return [0] * THREAD_COUNT

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

    for i in range(len(layers[0])):
        vertex_id = layers[0][i]
        graph.vs[vertex_id]['p'] = int(i / len(layers[0]) * THREAD_COUNT)

    heavinesses = []
    cross_thread_read = []
    in_thread_read = []
    in_thread_write = []
    pbar = tqdm(total=len(graph.vs))
    for layer in layers[1:]:
        heavinesses.append(np.zeros(shape=(THREAD_COUNT,)))
        cross_thread_read.append(np.zeros(shape=(THREAD_COUNT,)))
        in_thread_read.append(np.zeros(shape=(THREAD_COUNT,)))
        in_thread_write.append(np.zeros(shape=(THREAD_COUNT,)))

        if SHUFFLE_DEPTH:
            np.random.shuffle(layer)

        layer_complexity = 0
        if DEPTH_LAYER_VERTEX_CHOICE_METHOD == 'dummy':
            layer_complexity += len(layer)
        elif DEPTH_LAYER_VERTEX_CHOICE_METHOD == 'backpack':
            for vertex_id in layer:
                for parent in graph.vs[vertex_id].neighbors(mode='in'):
                    layer_complexity += parent['w']
        elif DEPTH_LAYER_VERTEX_CHOICE_METHOD == 'smart_backpack':
            for vertex_id in layer:
                thread = graph.vs[vertex_id]['p']
                for parent in graph.vs[vertex_id].neighbors(mode='in'):
                    if parent['p'] == thread:   
                        layer_complexity += parent['w']
                    else:
                        layer_complexity += parent['w'] * LOSS1 + LOSS2
        else:
            print_freindly('Плохой inside_layer_schedule:', DEPTH_LAYER_VERTEX_CHOICE_METHOD)
            quit(1)

        cumsum = 0
        for i in range(len(layer)):
            vertex_id = layer[i]
            vertex = graph.vs[vertex_id]

            thread = int(cumsum / max(layer_complexity, 1) * THREAD_COUNT)

            if DEPTH_LAYER_VERTEX_CHOICE_METHOD == 'dummy':
                cumsum += 1 
            elif DEPTH_LAYER_VERTEX_CHOICE_METHOD == 'backpack':
                cumsum += np.sum([parent['w'] for parent in vertex.neighbors(mode='in')])
            elif DEPTH_LAYER_VERTEX_CHOICE_METHOD == 'smart_backpack':
                for parent in vertex.neighbors(mode='in'):
                    if parent['p'] == thread:   
                        cumsum += parent['w']
                    else:
                        cumsum += parent['w'] * LOSS1 + LOSS2
            else:
                print_freindly('Плохой inside_layer_schedule:', DEPTH_LAYER_VERTEX_CHOICE_METHOD)
                quit(1)

            for parent in vertex.neighbors(mode='in'):
                if parent['p'] == thread:
                    in_thread_read[-1][thread] += parent['w']
                else:
                    cross_thread_read[-1][thread] += parent['w']
                in_thread_write[-1][thread] += parent['w']

            graph.vs[vertex_id]['p'] = thread

            heavinesses[-1][thread] += sum(parent['w'] for parent in vertex.neighbors(mode='in'))

        pbar.update(len(layer))
    pbar.close()

    return layers, heavinesses, in_thread_read, cross_thread_read, in_thread_write

# def get_tree(graph, root_id):
#     root = graph.vs[root_id]
    
#     ret = set([root_id])
#     children = set()
#     for child in root.neighbors(mode='out'):
#         child_id = child.index

#         if child_id in children:
#             continue

#         ret.update(get_tree(graph=graph, root_id=child_id))
#         children.add(child_id)

#     return ret

# def cut_graph_recursive(graph, turn2vertex_id):
#     if len(turn2vertex_id) < 1000:
#         cut_graph_greedy(turn2vertex_id)
#     else:
#         root_id = np.random.choice(turn2vertex_id)

#         vertices = get_tree(graph, root_id)

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
        layers, _, _, _, _ = cut_graph_depth(graph=graph)

        if __KILL_LAYERS:
            print_freindly('__KILL_LAYERS == True')

            if __EXTRACTED_LAYER_START != -1 or __EXTRACTED_LAYER_STOP != -1:
                print_freindly('Не реализовано')
                quit(1)

            for layer_num in tqdm_friendly(range(1,len(layers) - __SURVIVE_DEPTH)):
                vertices = sum(layers[layer_num:layer_num+__SURVIVE_DEPTH], [])
                subgraph = graph.subgraph(vertices)

                layers_choosen = list(range(layer_num, layer_num+__SURVIVE_DEPTH)),
                layers_sizes = [len(layer) for layer in layers[layer_num:layer_num+__SURVIVE_DEPTH]],
                total_vertices = len(vertices)
                
                if not os.path.exists('cutted_graphs'):
                    os.mkdir('cutted_graphs')

                with open(
                    os.path.join('cutted_graphs',
                                 os.path.basename(IN_PATH).split('.')[0] + '_' + \
                                                  str(layer_num) + '_' + \
                                                  str(layers_choosen)[1:-2] + '_' + \
                                                  str(layers_sizes)[1:-2] + '_' + \
                                                  str(total_vertices) + '.json'),
                    'w') as fd:

                    json.dump({
                            'node_weights' : list(subgraph.vs['w']),
                            'edges' : list([(e.target, e.source) for e in subgraph.es]), #### Внимание на порядок вершин!
                            'reg_edges' : [],
                            'nodes_parents' : [],
                            'modules_parents' : []
                        }, fd, indent=4)
                
            print_freindly('Done!')

            quit(0)
        else:
            layers, heavinesses, in_thread_read, cross_thread_read, in_thread_write = cut_graph_depth(graph=graph)

        memory_order = sum(layers, [])
    elif MODE == 4:
        with open(IN_PATH, 'r') as fd:
            graph_raw_ = json.load(fd)

        schedule = graph_raw_['schedule']
        sync_poins = graph_raw_['sync_points']

        THREAD_COUNT_ = len(schedule)

        reads = [0] * THREAD_COUNT_
        writes = [0] * THREAD_COUNT_
        syncs = [0] * THREAD_COUNT_
        ops = []
        full_ops = []
        sps = []

        for thread in range(THREAD_COUNT_):
            curr_ops = 0
            curr_full_ops = 0

            ops.append([])
            full_ops.append([])
            sps.append([])

            for op in schedule[thread]:
                if op[0] == 0:
                    reads[thread] += np.sum([vertex['w'] for vertex in graph.vs[op[1]].neighbors(mode='in')])
                    writes[thread] += graph.vs[op[1]]['w']

                    curr_ops += 1
                    curr_full_ops += int(np.sum([vertex['w'] for vertex in graph.vs[op[1]].neighbors(mode='in')]))
                elif op[0] == 1:
                    syncs[thread] += 1

                    sps[-1].append([len(sync_poins[op[1]][0]), len(sync_poins[op[1]][1])])
                    ops[-1].append(curr_ops)
                    full_ops[-1].append(curr_full_ops)

                    curr_ops = 0
                    curr_full_ops = 0
                else:
                    print_freindly('Плохое расписание')
                    quit(1)
    elif MODE == 5:
        print_freindly('Пользуюсь однопоточным жадным кэшированием')

        precomputed = [vertex.index for vertex in graph.vs if vertex.degree(mode='in') == 0]
        schedule = []

        layer = Layer(5000)
        layer.init_graph(len(graph.vs))
        for edge in graph_raw['edges']:
            layer.add_edge(edge[0], edge[1])
        layer.set_weights(list(graph.vs['w']))
        for vertex_id in precomputed:
            layer.set_score(vertex_id, graph.vs[vertex_id]['w'])
        layer.init_cache(MEM_SIZE)
        if np.amax(graph.vs['w']) > MEM_SIZE:
            print_freindly('Размер кэша меньше наибольшего веса среди вершин')
            quit(1)
        layer.start()

        print_freindly('Главный цикл')

        for i in tqdm_friendly(range(nc)):
            schedule.append(layer.step())

        memory_order = list(range(nc))
    elif MODE == 6:
        heaviness = cut_graph_random(graph=graph, turn2vertex_id=turn2vertex_id)

        memory_order = list(range(len(graph.vs)))

        cost = np.amax(heaviness)
    else:
        print_freindly('Неизвестный MODE:', MODE)
        quit(1)

    #
    #
    # Проверка расписания
    #
    #

    print_freindly('Проверяю расписание')
    if MODE in [1, 2, 6]:
        if len(turn2vertex_id) != len(set(turn2vertex_id)):
            print_freindly('В построенном расписании есть повторяющиеся вершины')
            quit(2)
        if np.amax(turn2vertex_id) != nc - 1 or np.amin(turn2vertex_id) != 0:
            print_freindly('В построенном расписании есть номера вершин, которых нет в графе')
            quit(2)
        print_freindly('TODO: Добавить полную проверку корректности расписания')
        print_freindly('OK')
    elif MODE in [3, 4]:
        print_freindly('Не умею проверять расписание для MODE == 3')
    elif MODE == 5:
        print_freindly('Дебаг1:', len(schedule) - len(set(schedule)))
        print_freindly('Дебаг2:', len(schedule) - nc)
    else:
        print_freindly('Неизвестный MODE:', MODE)
        quit(1)

    #
    #
    # Метрики
    #
    #
    
    if MODE in [1, 2, 6]:
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
        print_freindly('Суммарно чтений внутри одного потока:', np.sum(in_thread_read, axis=0).tolist())
        print_freindly('Суммарно чтений между потоками:', np.sum(cross_thread_read, axis=0).tolist())
        print_freindly('Суммарно записей:', np.sum(in_thread_write, axis=0).tolist())
        # print_freindly('vals1:', json.dumps([x.tolist() for x in in_thread_read]))
        # print_freindly('vals2:', json.dumps([x.tolist() for x in cross_thread_read]))
        # print_freindly('vals3:', json.dumps([x.tolist() for x in in_thread_write]))
    elif MODE == 4:
        print(json.dumps({
            'syncs' : np.array(syncs, dtype=int).tolist(),
            'max_syncs' : max(np.array(syncs, dtype=int).tolist()),
            'reads' : np.array(reads, dtype=int).tolist(),
            'writes' : np.array(writes, dtype=int).tolist(),
            'ops' : ops,
            'full_ops' : full_ops,
            'sync_points' : sps
            }))
    elif MODE == 5:
        print_freindly('Нет метрик')
    else:
        print_freindly('Неизвестный MODE:', MODE)
        quit(1)

    #
    #
    # Перевод в json
    #
    #

    print_freindly('Преобразую расписание к стандартному виду')

    if MODE in [1, 2, 6]:
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

        print_freindly(f'Исполльзовано {len(sync_points)} синхронизаций')
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
    elif MODE == 4:
        print_freindly('Это не требуется')
        quit(0)
    elif MODE == 5:
        schedule = [[[0, vertex_id] for vertex_id in schedule]]
        sync_points = []
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Videos to images')
    parser.add_argument('threads', type=int, help='Число потоков в расписании')
    parser.add_argument('LOSS1', type=float, help='LOSS1')
    parser.add_argument('LOSS2', type=float, help='LOSS2')
    parser.add_argument('in_file', type=str, help='Входной граф')
    parser.add_argument('out_file', type=str, help='Выходное расписание')
    parser.add_argument('--mem_size',
                        type=int,
                        default=64,
                        help='Размер кэша [КБ]')
    parser.add_argument('--shuffle_layers',
                        type=bool,
                        default=False,
                        help='Перемешивать вершины в слоях послойного расписания')
    parser.add_argument('--inside_layer_schedule',
                        type=str,
                        choices=['dummy', 'backpack', 'smart_backpack'],
                        default='backpack',
                        help='Режим распределения вершин в слое послойного расписания')
    parser.add_argument('--mode',
                        type=int,
                        choices=[1, 2, 3, 4, 5, 6],
                        default=3,
                        help='Выбор алгоритма построения расписания')
    parser.add_argument('--survive_depth',
                        type=int,
                        default=2,
                        help='Число вырезаемых слоев')
    parser.add_argument('--kill_layers',
                        type=bool,
                        default=False,
                        help='[Отладка] убрать из графа в послойном расписании все слои кроме двух')
    parser.add_argument('--extracted_layer_start',
                        type=int,
                        default=-1,
                        help='[Отладка] извлекаемые из графа слои, начало диапазона (номер первого слоя подграфа)')
    parser.add_argument('--extracted_layer_stop',
                        type=int,
                        default=-1,
                        help='[Отладка] извлекаеыме из графа слои, конец диапазона (номер первого слоя подграфа)')
    args = parser.parse_args()

    # Основное
    THREAD_COUNT = args.threads
    LOSS1 = args.LOSS1
    LOSS2 = args.LOSS2
    IN_PATH = args.in_file
    OUT_PATH = args.out_file
    MODE = args.mode
    SHUFFLE_DEPTH = args.shuffle_layers
    DEPTH_LAYER_VERTEX_CHOICE_METHOD = args.inside_layer_schedule
    MEM_SIZE = args.mem_size

    # Сообщения
    FRIENDLY = True
    TQDM_FRIENDLY = True

    # Свойства режима 2
    MODE2_ITER = 1000

    # Свойства режима 3
    __KILL_LAYERS = args.kill_layers
    __SURVIVE_DEPTH = args.survive_depth
    __EXTRACTED_LAYER_START = args.extracted_layer_start
    __EXTRACTED_LAYER_STOP = args.extracted_layer_stop

    main()