import json

import numpy as np

import matplotlib.pyplot as plt

if __name__ == '__main__':
    fd = open('result.json', 'r')
    data = json.load(fd)
    fd.close()

    x = np.array(data['x'])
    y1 = np.array(data['y1'])
    y2 = np.array(data['y2'])

    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.bar(np.array([i + 1 for i in range(len(x))]) - width / 2, y1, width=width, label='greedy', color='green')
    ax.bar(np.array([i + 1 for i in range(len(x))]) + width / 2, y2, width=width, label='random', color='red')

    ax.set_xticks([i + 1 for i in range(len(x))])
    ax.set_xticklabels(list(map(str, x)))

    plt.xlabel('Threads')
    plt.ylabel('Multithread / Single thread')

    plt.legend()

    plt.tight_layout()
    plt.savefig('perfomance.png')

    plt.clf()