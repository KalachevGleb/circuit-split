import json
import sys

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

# TODO
# Комментарии

filename = 'dep_graph-600K.json'

LOSS = 100000
THREAD_COUNT = 4

def main():
    print()
    print('Reading...')

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

    single_thread_time = sum(graph.vs['w'])
    print('Cost in single-thread computation:', single_thread_time)

    print()
    print('Greedy algorithm:')

    time_per_thread = [0] * THREAD_COUNT
    iter = 0
    for vertex_id in tqdm(turn2vertex_id):

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
    print('Cost per thread:', cost_greedy)
    print('Overhead:', str(sum(cost_greedy) - np.sum(graph.vs['w'])) + ',', str(round(100 * (sum(cost_greedy) / single_thread_time - 1), 3)) + '%')

    print('Creating dump')

    fd = open('cut.txt', 'w')

    vertex_id2turn = [None for _ in range(len(turn2vertex_id))]
    for i in range(len(turn2vertex_id)):
        vertex_id2turn[turn2vertex_id[i]] = i

    for vertex_id in tqdm(turn2vertex_id):

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
            else:
                fd.write(str(vertex_id2turn[parent.index]))

        fd.write('\n')

    fd.close()

if __name__ == '__main__':
    main()