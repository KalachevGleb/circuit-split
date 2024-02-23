# This script generates certain graphs for cirtain standard circuits, e.g. sorting networks.

import json


class BitonicSortGraph:
    def __init__(self, logn):
        self.n = 2 ** logn
        self.logn = logn
        self.edges = []
        self.last = list(range(self.n))
        self.curr_node = self.n
        self.edges = []
        self.reg_edges = []

        self.generate()

    def nextnode(self, a):
        self.last[a] = self.curr_node
        self.curr_node += 1
        return self.curr_node - 1

    def cmpedges(self, a, b):  # dependency edges corresponding to sorting pair of elements at positions a and b
        preva = self.last[a]
        prevb = self.last[b]
        curra = self.nextnode(a)
        currb = self.nextnode(b)
        self.edges.extend([[curra, preva], [curra, prevb], [currb, preva], [currb, prevb]])

    def generate_small_part(self, start, end):
        half = (end - start) // 2
        for i in range(half):
            self.cmpedges(start + i, end - i - 1)
        if half > 1:
            self.generate_small_part(start, start + half)
            self.generate_small_part(start + half, end)

    def generate_part(self, start, end):
        half = (end - start) // 2
        for i in range(half):
            self.cmpedges(start + i, end - i - 1)
        if half > 1:
            self.generate_small_part(start, start + half)
            self.generate_small_part(start + half, end)

    def generate(self):
        for i in range(1, self.logn+1):
            step = 2 ** i
            for j in range(0, self.n, step):
                self.generate_part(j, j + step)

        for i in range(self.n):
            self.reg_edges.append([i, self.last[i]])

    def graph(self):
        g = {
            'node_weights': [1] * self.curr_node,
            'edges': self.edges,
            'reg_edges': self.reg_edges
        }
        return g

    def one_thread_schedule(self):
        g = self.graph()
        sch = {
            'graph': g,
            'memory_order': list(range(self.curr_node)),
            'schedule': [[[0, i] for i in range(self.n, self.curr_node)]],  # all nodes are scheduled in the same thread
            'sync_points': [] # no sync points in one-thread schedule
        }
        return sch

    def schedule(self, nthreads):
        if nthreads == 1:
            return self.one_thread_schedule()
        raise NotImplementedError('Only one thread schedule is currently implemented for bitonic sort')


def main():
    # create directory for output
    import os
    if not os.path.exists('output'):
        os.makedirs('output')

    for logn in range(1, 15):
        graph = BitonicSortGraph(logn)
        with open(f'output/bitonic_sort_{logn}.json', 'w') as f:
            json.dump(graph.graph(), f)
        with open(f'output/bitonic_sort_{logn}_one_thread.json', 'w') as f:
            json.dump(graph.one_thread_schedule(), f)


if __name__ == '__main__':
    main()
