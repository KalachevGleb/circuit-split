import json
import sys

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

# TODO
#

FILENAME_IN = '../gen_graphs/output/bitonic_sort_7.json'
FRIENDLY = True
MODE = 0

def print_freindly(*msg):
    if FRIENDLY:
        print(*msg)

def main():

    fd = open(FILENAME_IN, 'r')
    graph_raw = json.load(fd)
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

    print_freindly('Дамп')

    fd = open('blob/out.json', 'w')
    json.dump({
        'graph' : graph_raw,
        'memory_order' : memory_order,
        'schedule' : [[[0, vertex_id] for vertex_id in schedule]],
        'sync_points' : []
    }, fd)
    fd.close()

    print_freindly('Готово! Have a nice day :)')

if __name__ == '__main__':
    main()