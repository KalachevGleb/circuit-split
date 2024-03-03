import json

import numpy as np

import matplotlib.pyplot as plt

def main():
    fd = open('blob/log.json', 'r')
    line = fd.read()
    data = json.loads(line)
    fd.close()

    data = np.array([entry['nsteps'] for entry in data])

    plt.plot(data)
    plt.savefig('blob/plot.png')

if __name__ == '__main__':
    main()