import sys
import os

import json

import numpy as np

import matplotlib.pyplot as plt

def main():
    fd = open(os.path.join(sys.argv[1]), 'r')
    line = fd.read()
    line = line[:-4] + line[-3:]
    data = json.loads(line)
    fd.close()

    data = np.array([entry['ns_per_node'] for entry in data])

    plt.plot(data)
    plt.savefig(os.path.join(sys.argv[1], 'plot.png'))

if __name__ == '__main__':
    main()