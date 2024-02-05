import json

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

filename = 'dep_graph-600K.json'

LOSS = 1000
THREAD_COUNT = 3

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

    print()
    print('Random cut:')

    graph.vs['t'] = None
    graph.vs['p'] = np.random.choice([i for i in range(THREAD_COUNT)], nc, p=[1. / THREAD_COUNT] * THREAD_COUNT)

    iter = 0

    time_per_thread = [0] * THREAD_COUNT
    for vertex_id in tqdm(turn2vertex_id):

        vertex = graph.vs[vertex_id]
        parents = vertex.neighbors(mode='in')

        if vertex['w'] == 0:
            vertex['t'] = 0
            continue

        thread = vertex['p']

        t = -1
        for parent in parents:
            if parent['p'] != thread:
                t = max(vertex['w'] + parent['t'] + LOSS, t)
            else:
                t = max(vertex['w'] + parent['t'], t)

        if t < time_per_thread[thread] + vertex['w']:
            t = time_per_thread[thread] + vertex['w']

        time_per_thread[thread] = t
        vertex['t'] = t

    cost_random = time_per_thread
    print('Cost per thread:', cost_random)
    print('Overhead:', str(sum(cost_random) - np.sum(graph.vs['w'])) + ',', str(round(100 * (sum(cost_random) / single_thread_time - 1), 3)) + '%')

    print()
    print('Improvement:', str(round((1 - (max(cost_greedy)) / max(cost_random)) * 100, 3)) + '%')

    print()
    print('Done!')

    return single_thread_time, max(cost_greedy), max(cost_random)

if __name__ == '__main__':
    x = [2 ** i for i in range(10)]
    y1 = []
    y2 = []

    for tc in x:
        THREAD_COUNT = tc

        single_thread_time, greedy_time, random_time = main()

        y1.append(greedy_time / single_thread_time)
        y2.append(random_time / single_thread_time)

    x = np.array(x)
    y1 = np.array(y1)
    y2 = np.array(y2)

    fd = open('result.json', 'w')
    fd.write(json.dumps({
        'x' : x.tolist(),
        'y1' : y1.tolist(),
        'y2' : y2.tolist()
    }))
    fd.close()