import sys
import os

import json

import numpy as np

import matplotlib.pyplot as plt

def main():
    with open(os.path.join(sys.argv[1]), 'r') as fd:
        line = fd.read()
        line = line[:-4] + line[-3:]
        data = json.loads(line)

    data = np.array([entry['ns_per_node'] for entry in data])

    plt.plot(data)
    plt.savefig(sys.argv[1] + '.png')

if __name__ == '__main__':
    main()