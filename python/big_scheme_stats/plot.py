import pickle

import numpy as np

from matplotlib import pyplot as plt
from matplotlib import rcParams

rcParams['figure.figsize'] = 20, 15

GRID_SIZE = 10
BINS = 50
ALPHA = 0.05
Q = 1.97196
N = 200

with open('log.pickle', 'rb') as fd:
    objects = pickle.load(fd)

data = dict()
commands = []
curr_command = ''
for obj in objects:
    if type(obj) == str:
        curr_command = obj
        commands.append(obj)
        data[curr_command] = []
    else:
        data[curr_command].append(obj)

cmd_lengths = [len(cmd) for cmd in commands]
print(cmd_lengths)

npns = {cmd : [] for cmd in commands}
for key, vals in data.items():
    npns[key] = [val['ns_per_node'] for val in vals]

exp_nums = [i for i in range(10) if '4 1 0' in commands[i]]

for exp_num in exp_nums:
    command = commands[exp_num]
    exp = np.array(npns[command])

    x_min, x_max = np.amin(exp), np.amax(exp)
    delta = x_max - x_min
    grid = np.linspace(x_min - delta / 7, x_max + delta / 7, GRID_SIZE)
    bins = [0] * GRID_SIZE

    for x in exp:
        bins[np.argmin(np.abs(grid - x))] += 1

    plot_data = sum([[grid[i]] * bins[i] for i in range(GRID_SIZE)], [])

    plt.hist(exp, bins=BINS, histtype='step')

    if exp.shape[0] != N:
        print('Пропускается эксперимент', exp_num, ' т.к. нет соответствующей квантили')
    else:
        mu = np.mean(exp)
        s = np.sqrt(np.sum((exp - mu) ** 2) / (N - 1))
        low = mu - Q * s / np.sqrt(N)
        high = mu + Q * s / np.sqrt(N)

        print(('[' + command + ']').ljust(max(cmd_lengths) + 5) +  'среднее: ' + str(round(mu, 3)) + \
              ', ди: [' + str(round(low, 3)) + ';' + str(round(high, 3)) + \
                '], размер ди: ' + str(round(high - low, 3)))

plt.xlim(0, None)
plt.legend(title='proba_density', loc='upper right', labels=commands)
plt.savefig('plot.png')