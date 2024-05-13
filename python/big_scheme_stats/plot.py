import pickle

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from matplotlib import rcParams

rcParams['figure.figsize'] = 15, 10

GRID_SIZE = 10
BINS = 20
ALPHA = 0.05
Q = 1.97196
N = 200

def stats(data, commands, key):
    means = []
    lows = []
    highs = []

    for command in commands:
        exp = np.array([entry[key] for entry in data[command]])

        mu = np.mean(exp)
        s = np.sqrt(np.sum((exp - mu) ** 2) / (N - 1))
        low = mu - Q * s / np.sqrt(N)
        high = mu + Q * s / np.sqrt(N)

        means.append(mu)
        lows.append(low)
        highs.append(high)

    return np.array(means), np.array(lows), np.array(highs)

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

commands = [cmd for cmd in commands if 'greedy' not in cmd]

exp_nums = list(range(len(commands)))
for key in ['ns_per_read']:

    plt.clf()

    for exp_num in exp_nums:
        command = commands[exp_num]
        exp = np.array([result[key] for result in data[commands[exp_num]]])

        x_min, x_max = np.amin(exp), np.amax(exp)

        plt.hist(exp, bins=BINS, histtype='step')
        
    plt.xlabel = key
    plt.ylabel = 'count'

    plt.xlim(0, None)
    plt.legend(title='~ Probability density', loc='upper left', labels=commands)

    plt.tight_layout()
    plt.savefig('hist_' + key + '.png')

for key in ['ns_per_read']:
    plt.clf()

    means, lows, highs = stats(data, commands, key)
    conf_intervals = (highs - lows) / 2

    widths = [0.1] * len(commands)
    x_ticks = np.arange(len(commands))

    fig, ax = plt.subplots()
    for i in range(len(commands)):
        bar = ax.bar(x_ticks[i], means[i], widths[i], yerr=conf_intervals[i])

    ax.set_ylabel(key)
    ax.set_title(key)
    #ax.set_xlabel('threads')
    ax.set_xticks(x_ticks)
    if len(commands) == 10:
        ax.set_xticklabels([1, 1, 2, 4, 2, 4, 2, 4, 2, 4])
    else:
        ax.set_xticklabels(commands)

    plt.legend(loc='upper right', labels=commands)

    plt.tight_layout()
    plt.savefig('bars_' + key + '.png')

if len(commands) == 10:
    print('Не печатаю таблицу; выход')

means, lows, highs = stats(data, commands, key)
conf_intervals = (highs - lows)

table = {
    '# потоков' : [cmd.split('_')[1] for cmd in commands],
    'тип' : ['_'.join(cmd.split('_')[2:]) for cmd in commands],
    'ср время' : means,
    'размер ди' : conf_intervals
}

df = pd.DataFrame(data=table)

print(df)