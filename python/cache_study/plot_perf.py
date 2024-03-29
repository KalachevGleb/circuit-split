import sys
import json
import os

import matplotlib.pyplot as plt

import numpy as np

if len(sys.argv) == 1:
    PATH = './blob'
else:
    PATH = sys.argv[1]

def main():
    with open(os.path.join(PATH, 'perf.json'), 'r') as fd:
        data = json.load(fd)

    misses = []
    refs = []
    l2_misses = []
    l2_refs = []
    for i in [2 ** j for j in range(13)]:
        misses.append(np.mean(data[str(i)]['cache-misses']))
        refs.append(np.mean(data[str(i)]['cache-references']))
        l2_misses.append(np.mean(data[str(i)]['l2_miss']))
        l2_refs.append(np.mean(data[str(i)]['l2_ref']))
    misses.append(np.mean(data['stock']['cache-misses']))
    refs.append(np.mean(data['stock']['cache-references']))
    l2_misses.append(np.mean(data['stock']['l2_miss']))
    l2_refs.append(np.mean(data['stock']['l2_ref']))

    fig, ax = plt.subplots()

    ax.set_xticks([i for i in range(len(misses))])
    ax.set_xticklabels([2 ** j for j in range(13)] + ['stock'])

    ax.plot(misses, label='cache-misses')
    ax.plot(refs, label='cache-references')
    ax.plot(l2_misses, label='l2-misses')
    ax.plot(l2_refs, label='l2-refs')
    
    ax.legend(loc='upper left')

    ax.set_xlabel('Рахмер кэша')
    ax.set_ylabel('События')

    plt.tight_layout()
    plt.savefig(os.path.join(PATH, 'misses.png'))

if __name__ == '__main__':
    main()