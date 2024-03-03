import json
import sys
import random

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

# TODO
#

FILENAME_IN = '../gen_graphs/output/bitonic_sort_11.json'
FRIENDLY = True
MODE = int(sys.argv[1])
MAX_SAMPLE_SIZE = 10
MEM_SIZE = int(sys.argv[2]) * 1024

class Cache:
    def __init__(self, max_size):
        self.max_size = max_size
        self.ids = []
        self.sizes = []

    def push(self, id, size):
        if size > self.max_size:
            self.ids = []
            self.sizes = []

            return
        elif id in self.ids:
            if self.ids[-1] == id:
                return
            else:
                pos = self.ids.index(id)

                self.ids[pos], self.ids[-1] = self.ids[-1], self.ids[pos]
                self.sizes[pos], self.sizes[-1] = self.sizes[-1], self.sizes[pos]

                return
        else:
            while self.max_size - sum(self.sizes) < size:
                del self.ids[0]
                del self.sizes[0]

            self.ids.append(id)
            self.sizes.append(size)

            return

    def __contains__(self, id):
        return id in self.ids
    
    def pos(self, id):
        if id not in self.ids:
            raise ValueError('Попытка найти в кэше переменную, которая в нем не содержится')
        
        return self.ids.index(id)
    
    def score(self, ids):
        ret = 0

        for id in set(ids):
            if id in self.ids:
                ret += self.sizes[self.ids.index(id)]

        return ret

def build_schedule_recursive(graph):
    if len(graph) <= 3:
        pass

    pass

def print_freindly(*msg):
    if FRIENDLY:
        print(*msg)

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
            cache.push(vertex.index, vertex['w'] * 4) #4 == sizeof(int)
            del curr_vertices[curr_vertices.index(vertex)]

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
                
    else:
        raise ValueError('Плохой MODE')

    print_freindly('Дамп')

    fd = open('blob/out.json', 'w')
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