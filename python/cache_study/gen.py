import json
import sys
import os
import random
import collections

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

import cpp
Cache = cpp.Cache
Layer = cpp.Layer

# TODO
# Добавить различные веса вершин

FILENAME_IN = sys.argv[5]
FRIENDLY = True
MODE = int(sys.argv[1])
MEM_SIZE = int(sys.argv[2]) * 1024
MAX_SAMPLE_SIZE = int(sys.argv[3])
PLOT_GRAPH = False

# class Cache:
#     def __init__(self, max_size):
#         self.max_size = max_size
#         self.ids = []
#         self.sizes = []

#     def push(self, id, size):
#         if size > self.max_size:
#             self.ids = []
#             self.sizes = []

#             return
#         elif id in self.ids:
#             if self.ids[-1] == id:
#                 return
#             else:
#                 pos = self.ids.index(id)

#                 self.ids[pos], self.ids[-1] = self.ids[-1], self.ids[pos]
#                 self.sizes[pos], self.sizes[-1] = self.sizes[-1], self.sizes[pos]

#                 return
#         else:
#             while self.max_size - sum(self.sizes) < size:
#                 del self.ids[0]
#                 del self.sizes[0]

#             self.ids.append(id)
#             self.sizes.append(size)

#             return

#     def __contains__(self, id):
#         return id in self.ids
    
#     def pos(self, id):
#         if id not in self.ids:
#             raise ValueError('Попытка найти в кэше переменную, которая в нем не содержится')
        
#         return self.ids.index(id)
    
#     def score(self, ids):
#         ret = 0

#         for id in set(ids):
#             if id in self.ids:
#                 ret += self.sizes[self.ids.index(id)]

#         return ret

def build_schedule_recursive(graph): #Потом
    if len(graph) <= 3:
        pass

    pass

def print_freindly(*msg):
    if FRIENDLY:
        print(*msg)
        sys.stdout.flush()

def progressbar_friendly(arg):
    if FRIENDLY:
        return tqdm(arg)
    else:
        return arg

def main():
    with open(FILENAME_IN, 'r') as fd:
        graph_raw = json.load(fd)
        graph_raw_copy = graph_raw.copy()

    nc = len(graph_raw['node_weights'])
    ec = len(graph_raw['edges'])

    graph_raw['edges'] = [(e[1], e[0]) for e in graph_raw['edges']]    

    graph = ig.Graph(nc, directed=True)
    graph.vs['w'] = graph_raw['node_weights']
    graph.add_edges(graph_raw['edges'])

    print_freindly('Прочитан граф на', len(graph.vs), 'вершин')

    if PLOT_GRAPH:
        ig.plot(graph,
                target='graph.pdf',
                vertex_size=20,
                bbox=(5000, 5000)
        )

    if MODE == 0:
        print_freindly('Пользуюсь стандартной топологической сортировкой')

        schedule = graph.topological_sorting(mode='out')

        print_freindly('Укладка в памяти стандартная')

        memory_order = list(range(nc))
    elif MODE == 1:
        print_freindly('Пользуюсь жадным алгоритмом')

        schedule = []
        cache = Cache(max_size=MEM_SIZE)

        curr_vertices = [vertex for vertex in graph.vs if vertex.degree(mode='in') == 0]
        for _ in range(len(graph.vs)):
            
            scores = []
            for vertex in random.sample(curr_vertices, k=min(MAX_SAMPLE_SIZE, len(curr_vertices))):
                ids = [parent.index for parent in vertex.neighbors(mode='in')]
                scores.append(cache.score(ids))

            vertex = curr_vertices[np.argmax(scores)]

            schedule.append(vertex.index)
            cache.push(vertex.index)
            del curr_vertices[np.argmax(scores)]

            for child in vertex.neighbors(mode='out'):
                if child in curr_vertices:
                    continue
                
                good = True
                for parent in child.neighbors(mode='in'):
                    if parent.index not in schedule:
                        good = False
                        break

                if good:
                    curr_vertices.append(child)
                    
        print_freindly('Укладка в памяти стандартная')

        memory_order = list(range(nc))
    elif MODE == 2:
        print_freindly('Пользуюсь второй версией жадного алгоритма')

        schedule = []
        cache = Cache(max_size=MEM_SIZE)

        graph.vs['codegree'] = [vertex.degree(mode='in') for vertex in graph.vs]

        curr_vertices = [vertex for vertex in graph.vs if vertex.degree(mode='in') == 0]
        for _ in progressbar_friendly(range(len(graph.vs))):
            
            scores = []
            for vertex in random.sample(curr_vertices, k=min(MAX_SAMPLE_SIZE, len(curr_vertices))):
                ids = [parent.index for parent in vertex.neighbors(mode='in')]
                scores.append(cache.score(ids))

            vertex = curr_vertices[np.argmax(scores)]

            schedule.append(vertex.index)
            cache.push(vertex.index)
            curr_vertices.remove(vertex)

            for child in vertex.neighbors(mode='out'):
                if child['codegree'] == 1:
                    curr_vertices.append(child)
                
                child['codegree'] -= 1
                    
        print_freindly('Укладка в памяти стандартная')

        memory_order = list(range(nc))
    elif MODE == 3:
        print_freindly('Пользуюсь третьей версией жадного алгоритма')

        schedule = []
        cache = Cache(MEM_SIZE)

        graph.vs['codegree'] = [vertex.degree(mode='in') for vertex in graph.vs]

        curr_vertices = set([vertex for vertex in graph.vs if vertex.degree(mode='in') == 0])
        for _ in progressbar_friendly(range(len(graph.vs))):
            
            min_score = 1000000000
            min_parents = None
            ####################################
            for _vertex in random.sample(list(curr_vertices), min(MAX_SAMPLE_SIZE, len(curr_vertices))):##############LISTLIST LIST LIST
            #############################################
                ids = [parent.index for parent in _vertex.neighbors(mode='in')]

                score = len(ids) - cache.antiscore(ids)
                if not cache.contains(_vertex.index):
                    score += _vertex['w']

                if score < min_score:
                    vertex = _vertex
                    min_score = score
                    min_parents = ids
                
            for parent_id in min_parents:
                cache.push(parent_id, vertex['w'])
            cache.push(vertex.index, vertex['w'])

            schedule.append(vertex.index)
            curr_vertices.remove(vertex)

            for child in vertex.neighbors(mode='out'):
                if child['codegree'] == 1:
                    curr_vertices.add(child)
                
                child['codegree'] -= 1
                    
        print_freindly('Укладка в памяти стандартная')

        memory_order = list(range(nc))
    elif MODE == 4:
        print_freindly('Пользуюсь четвертой версией жадного алгоритма')

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
        print(np.amax(graph.vs['w']), MEM_SIZE)
        layer.start()

        print_freindly('Главный цикл')

        for i in progressbar_friendly(range(nc)):#len(graph.vs)):
            schedule.append(layer.step())

        print_freindly()
        print_freindly('Дебаг:', len(schedule) - len(set(schedule)))

        print_freindly()
        print_freindly('Укладка в памяти стандартная')

        memory_order = list(range(nc))
    # elif MODE == 5:
    #     print_freindly('Пользуюсь четвертой версией жадного алгоритма')

    #     precomputed = [vertex.index for vertex in graph.vs if vertex.degree(mode='in') == 0]
    #     schedule = []

    #     layer = Layer(5000)
    #     layer.init_graph(len(graph.vs))
    #     for edge in graph_raw['edges']:
    #         layer.add_edge(edge[0], edge[1])
    #     layer.set_weights(list(graph.vs['w']))
    #     for vertex_id in precomputed:
    #         layer.set_score(vertex_id, graph.vs[vertex_id]['w'])
    #     layer.init_cache(MEM_SIZE)
    #     print(np.amax(graph.vs['w']), MEM_SIZE)
    #     layer.start()

    #     print_freindly('Главный цикл')

    #     for i in progressbar_friendly(range(nc)):#len(graph.vs)):
    #         schedule.append(layer.step())

    #     print_freindly()
    #     #print_freindly('Расписание:', schedule)
    #     print_freindly('Дебаг:', len(schedule) - len(set(schedule)))

    #     print_freindly()
    #     print_freindly('Укладка в памяти')

    #     hh = layer.cache_history()
        
    #     pair2freq = dict()
    #     prev = hh[0]
    #     for curr in hh[1:]:
    #         if prev == curr:
    #             continue

    #         p = (min(prev, curr), max(prev, curr))

    #         if p not in pair2freq:
    #             pair2freq[p] = 1
    #         else:
    #             pair2freq[p] += 1

    #     freq2pairs = dict()
    #     for key, val in pair2freq:
    #         if val not in pair2freq:
    #             freq2pairs[val] = [key]
    #         else:
    #             freq2pairs[val].append(key)

    #     # class Line(object):
    #     #     def __init__(self):
    #     #         self.a = None
    #     #         self.b = None
    #     #         self.mem = collections.deque()
            
    #     #     def push_right(self, pair):
    #     #         if len(self.mem) == 0:
    #     #             self.mem.append(pair)
    #     #             self.a = pair[0]
    #     #             self.b = pair[1]
    #     #         else:
    #     #             if pair[0]

    #     freqs = sorted(list(freq2pairs.keys()))[::-1]
    #     used = set()
    #     for freq in freqs:
    #         deques = []
    #         side2deque_num = dict()

    #         pairs = pair2freq[freq]
    #         for pair in pairs:
    #             a = pair[0]
    #             b = pair[1]

    #             if a in used and b in used:
    #                 continue
    #             elif a in used:
    #                 if a in side2deque_num:
    #                     num = side2deque_num[a]

    #                     if deques[num][0] == a:
    #                         deques[num].appendleft(b)
    #                     else:
    #                         deques[num].append(b)

    #                     del side2deque_num[a]
    #                     side2deque_num[b] = num
    #                 else:
    #                     side2deque_num[a] = collections.deque([a, b])
    #             elif b in used:
    #                 if b in side2deque_num:
    #                     num = side2deque_num[b]

    #                     if deques[num][0] == b:
    #                         deques[num].appendleft(a)
    #                     else:
    #                         deques[num].append(a)
    #             else: #a is not used and b is not used

    #             used.add(a)
    #             used.add(b)


    #             if a not in side2deque_num and b not in side2deque_num:
    #                 deques.append(collections.deque([a, b]))
    #                 side2deque_num[a] = len(deques) - 1
    #                 side2deque_num[b] = len(deques) - 1
    #             elif a in side2deque_num:
    #                 d_num = side2deque_num[a]








    #     memory_order = list(range(nc))
    else:
        raise ValueError('Плохой MODE')

    print_freindly('Дамп')

    if not FRIENDLY:
        print(json.dumps({
            'graph' : graph_raw_copy,
            'memory_order' : memory_order,
            'schedule' : [[[0, vertex_id] for vertex_id in schedule]],
            'sync_points' : []
        }))
    else:
        if not os.path.exists('blob'):
            os.mkdir('blob')
            
        with open(sys.argv[4], 'w') as fd:
            json.dump({
                'graph' : graph_raw_copy,
                'memory_order' : memory_order,
                'schedule' : [[[0, vertex_id] for vertex_id in schedule]],
                'sync_points' : []
            }, fd)

    print_freindly('Готово! Have a nice day :)')

if __name__ == '__main__':
    main()