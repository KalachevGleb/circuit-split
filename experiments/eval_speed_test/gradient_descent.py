import json
import sys
import os

import igraph as ig
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt

import torch
from torch.optim import SGD

FloatTensor = torch.FloatTensor

BATCH_SIZE = 10
LR = 0.01
STEP_COUNT = 100

# TODO
# Комментарии

filename = 'dep_graph.json'

def sigmoid(x):
  return 1 / (1 + np.exp(-x))

def main():
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

    vertex_id2turn = [None for _ in range(len(turn2vertex_id))]                 
    for i in range(len(turn2vertex_id)):                                        
        vertex_id2turn[turn2vertex_id[i]] = i

    single_thread_time = sum(graph.vs['w'])

    print('Cost in single-thread computation:', single_thread_time)

    print('Initializaton...')

    weights = FloatTensor(np.random.uniform(size=len(graph.vs)))

    optimizer = SGD(params=[weights], lr=LR)

    print('Training')

    for step in tqdm(range(STEP_COUNT)):
        schedule = sigmoid(weights.detach().cpu().numpy())

        loss = FloatTensor(np.array([0]))

        for batch_num in range(BATCH_SIZE):
            graph.vs['p'] = [np.random.choice([0, 1], p=[p,1-p]) for p in schedule]

            fd = open('cut.txt', 'w')                                                  

            for vertex_id in turn2vertex_id: #tqdm(turn2vertex_id):                                  
                                                                                        
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

            score = float(os.popen('./work cut.txt').read().strip())

            print(score)

if __name__ == '__main__':
    main()