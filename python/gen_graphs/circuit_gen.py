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


class SimpleCircuitGraph:
    def __init__(self, n, depth):
        self.n = n
        self.depth = depth
        self.nv = n*(depth+1)
        self.edges = []
        self.reg_edges = []
        for i in range(depth):
            off = i*n
            for j in range(n):
                self.edges.append([off+n+j, off+j])
                self.edges.append([off+n+j, off+(j+1)%n])
        for i in range(n):
            self.reg_edges.append([i, depth*n+i])

    def graph(self):
        g = {
            'node_weights': [1] * self.nv,
            'edges': self.edges,
            'reg_edges': self.reg_edges
        }
        return g

    def one_thread_schedule(self):
        g = self.graph()
        sch = {
            'graph': g,
            'memory_order': list(range(self.nv)),
            'schedule': [[[0, i] for i in range(self.n, self.nv)]],  # all nodes are scheduled in the same thread
            'sync_points': [] # no sync points in one-thread schedule
        }
        return sch

    def schedule(self, nthreads):
        g = self.graph()
        sync_points = [[[i],[(i+1)%nthreads]] for i in range(nthreads)] if nthreads > 1 else []
        morder = [i*self.n + j for j in range(self.n) for i in range(self.depth+1)]
        schedule = [[] for i in range(nthreads)]
        for i in range(nthreads):
            b, e = self.n*i//nthreads, self.n*(i+1)//nthreads
            for j in range(b, e+self.depth):
                if j == b+self.depth+1 and nthreads > 1:
                    schedule[i].append([1, (i + nthreads - 1) % nthreads])  # sync point (signal)
                if j == e and nthreads > 1:
                    schedule[i].append([1, i])  # sync point (wait)
                for k in range(self.depth+1):
                    jk = j - k
                    if b <= jk < e:
                        schedule[i].append([0, jk+k*self.n])

        sch = {
            'graph': g,
            'memory_order': morder,
            'schedule': schedule,
            'sync_points': sync_points
        }
        return sch


def gen_simple_circuits(nrange, depth, nth=(1,)):
    for n in nrange:
        graph = SimpleCircuitGraph(n, depth)
        with open(f'output/simple_circuit_{n}_{depth}.json', 'w') as f:
            json.dump(graph.graph(), f)
        for nthreads in nth:
            with open(f'output/simple_circuit_n{n}_d{depth}_th{nthreads}.json', 'w') as f:
                json.dump(graph.schedule(nthreads), f)


def main():
    # create directory for output
    import os
    if not os.path.exists('output'):
        os.makedirs('output')

    #gen_simple_circuits([10],2,[1,2,4])
    # generate simple circuits
    gen_simple_circuits([2**i for i in range(10, 18)], 20, [1, 2, 4, 8, 16])
    #gen_simple_circuits([2 ** i for i in range(16, 21)], 2, [1, 2, 4, 8, 16])

    for logn in range(1, 15):
        graph = BitonicSortGraph(logn)
        with open(f'output/bitonic_sort_{logn}.json', 'w') as f:
            json.dump(graph.graph(), f)
        with open(f'output/bitonic_sort_{logn}_one_thread.json', 'w') as f:
            json.dump(graph.one_thread_schedule(), f)

    return 0


if __name__ == '__main__':
    main()
