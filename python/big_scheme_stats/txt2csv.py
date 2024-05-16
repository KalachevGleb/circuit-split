import json
import sys

import pandas as pd
import numpy as np

N = 200
ALPHA = 0.05
Q = 1.97196

def stats(arr):
    mu = np.mean(arr)
    s = np.sqrt(np.sum((np.array(arr) - mu) ** 2) / (N - 1))
    low = mu - Q * s / np.sqrt(N)
    high = mu + Q * s / np.sqrt(N)

    return mu, high - low

if len(sys.argv) == 1:
    print('Ожидался txt; выход')
    quit(1)

objects = []
with open(sys.argv[1], 'r') as fd:
    curr_text = ""
    while True:
        try:
            line = fd.readline()
            if len(line) == 0: 
                break
        except:
            break
        
        curr_text = curr_text + line
        try:
            objects.append(json.loads(curr_text))
            curr_text = ""
            continue
        except:
            continue

result = []

curr_shift = 0
while True:
    if curr_shift == len(objects):
        break
    if curr_shift > len(objects):
        print('Число объектов не кратно 2 + 2 * N')
        quit(1)

    name = objects[curr_shift]
    top = objects[curr_shift + 1]

    perfs = dict()
    nprs = []
    for j in range(N):

        perf = objects[curr_shift + j + 2]
        for key in perf.keys():
            if key not in perfs.keys():
                perfs[key] = []

            perfs[key].append(int(perf[key].split(key)[0].replace(' ', '').replace('\u202f', '')))

        nprs.append(float(objects[curr_shift + j + 2 + N]['ns_per_read']))

    perfs_ = dict()
    for key in perfs.keys():
        perfs_[key + '_mean'], perfs_[key + '_ci'] = stats(perfs[key])
    perfs = perfs_

    nprs_mean, nprs_ci = stats(nprs)

    result.append({'name' : name} | top | perfs | {'nprs_mean' : nprs_mean, 'nprs_ci' : nprs_ci})

    curr_shift += 2 + 2 * N
 
df = pd.DataFrame(result)
print(df.head())
print(list(df))
