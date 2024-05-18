import json
import sys
import os

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

def run(path):
    objects = []
    with open(path, 'r') as fd:
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

        name = objects[curr_shift] + '_' + os.path.basename(path)[:-4]
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
        perfs_['промахи ср'], perfs_['промахи ди'] = stats(perfs['cache-misses'])
        perfs_['исп кэша ср'], perfs_['исп кэша ди'] = stats(perfs['cache-references'])
        perfs_['промахи L2 ср'], perfs_['промахи L2 ди'] = stats(perfs['l2_rqsts.all_demand_miss'])
        perfs_['исп L2 ср'], perfs_['исп L2 ди'] = stats(perfs['l2_rqsts.all_demand_references'])
        perfs = perfs_

        nprs_mean, nprs_ci = stats(nprs)

        result.append({'name' : name} | top | perfs | {'nprs_mean' : nprs_mean, 'nprs_ci' : nprs_ci})

        curr_shift += 2 + 2 * N

    return pd.DataFrame(result)

if __name__ == '__main__':

    dfs = []

    for filename in os.listdir('13to17'):
        dfs.append(run(os.path.join('13to17', filename)))

    df = pd.concat(dfs, axis=0).reset_index()
    del df['index']

    print(df)
    print(list(df))

    df.to_csv(os.path.join('13to17', 'table.csv'))