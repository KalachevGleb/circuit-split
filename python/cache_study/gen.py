import json
import sys
import os
import random

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

import cpp
Cache = cpp.Cache
Layer = cpp.Layer

# TODO
# Добавитьразличные веса вершин

FILENAME_IN = './dep_graph-600K-new.json'
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
    fd = open(FILENAME_IN, 'r')
    graph_raw = json.load(fd)
    graph_raw_copy = graph_raw.copy()
    fd.close()

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
        #print_freindly('Расписание:', schedule)
        print_freindly('Дебаг:', len(schedule) - len(set(schedule)))

        print_freindly()
        print_freindly('Укладка в памяти стандартная')

        memory_order = list(range(nc))
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
            
        fd = open(sys.argv[4], 'w')
        json.dump({
            'graph' : graph_raw_copy,
            'memory_order' : memory_order,
            'schedule' : [[[0, vertex_id] for vertex_id in schedule]],
            'sync_points' : []
        }, fd)
        fd.close()

    print_freindly('Готово! Have a nice day :)')

if __name__ == '__main__':
    main()