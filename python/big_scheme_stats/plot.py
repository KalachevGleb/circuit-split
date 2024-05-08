import pickle

import numpy as np

import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib import rcParams

rcParams['figure.figsize'] = 20, 15

GRID_SIZE = 10

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

npns = {cmd : [] for cmd in commands}
for key, vals in data.items():
    npns[key] = [val['ns_per_node'] for val in vals]

exp_nums = list(range(10))
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

    sns.set_style('whitegrid')
    plot = sns.kdeplot(plot_data)

fig = plot.get_figure()
plt.legend(title='proba_density', loc='upper right', labels=commands)
fig.savefig('plot.png')