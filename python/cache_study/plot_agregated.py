import sys
import os

import json

import numpy as np

import matplotlib.pyplot as plt

STOCK_INDICES = [i for i in range(20)]
GREEDY_INDICES = [i for i in range(20, 40)]

def main():
    filenames = list(map(str, [1, 2, 4, 8, 16, 32, 64, 128, 131072]))

    ns_per_node = {'stock' : [], 'greedy' : []}
    ns_per_read = {'stock' : [], 'greedy' : []}
    mem_sizes = [int(fn) for fn in filenames]

    for fn in filenames:
        with open(os.path.join('blob', fn), 'r') as fd:
            line = fd.read()
            line = line[:-4] + line[-3:]
            data = json.loads(line)

            ns_per_node['stock'].append(np.mean(np.array([entry['ns_per_node'] for entry in data])[STOCK_INDICES]))
            ns_per_node['greedy'].append(np.mean(np.array([entry['ns_per_node'] for entry in data])[GREEDY_INDICES]))
            ns_per_read['stock'].append(np.mean(np.array([entry['ns_per_read'] for entry in data])[STOCK_INDICES]))
            ns_per_read['greedy'].append(np.mean(np.array([entry['ns_per_read'] for entry in data])[GREEDY_INDICES]))

    width = 0.35
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

    ax1.bar(np.array([i + 1 for i in range(len(mem_sizes))]) - width / 2, ns_per_node['stock'], width=width, label='stock', color='#364b44')
    ax1.bar(np.array([i + 1 for i in range(len(mem_sizes))]) + width / 2, ns_per_node['greedy'], width=width, label='greedy', color='#D64161')
    ax1.set_xticks([i + 1 for i in range(len(mem_sizes))])
    ax1.set_xticklabels(mem_sizes)

    ax2.bar(np.array([i + 1 for i in range(len(mem_sizes))]) - width / 2, ns_per_read['stock'], width=width, label='stock', color='#3B1877')
    ax2.bar(np.array([i + 1 for i in range(len(mem_sizes))]) + width / 2, ns_per_read['greedy'], width=width, label='greedy', color='#DA5A2A')
    ax2.set_xticks([i + 1 for i in range(len(mem_sizes))])
    ax2.set_xticklabels(mem_sizes)

    ax1.set_xlabel('Mem size')
    ax1.set_ylabel('Mean ns_per_node')
    ax1.legend()

    ax2.set_xlabel('Mem size')
    ax2.set_ylabel('Mean ns_per_read')
    ax2.legend()

    plt.tight_layout()
    plt.savefig('blob/agregated.png')

if __name__ == '__main__':
    main()
