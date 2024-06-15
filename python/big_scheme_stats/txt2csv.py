import json
import sys
import os

import pandas as pd
import numpy as np

N = 50
ALPHA = 0.05 # N=200
Q = 1.97196 # N=200

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

        params = [
            "cache-misses",
            "cache-references",
            "L1-dcache-load-misses",
            "L1-dcache-loads",
            "l2_rqsts.all_demand_miss",
            "l2_rqsts.all_demand_references",
            "l2_rqsts.miss",
            "l2_rqsts.references",
            "LLC-load-misses",
            "LLC-loads",
            "cycles",
            "cycle_activity.cycles_l1d_miss",
            "cycle_activity.cycles_l2_miss",
            "cycle_activity.cycles_l3_miss",
            "cycle_activity.stalls_l1d_miss",
            "cycle_activity.stalls_l2_miss",
            "cycle_activity.stalls_l3_miss",
            "cycle_activity.cycles_mem_any",
            "cycle_activity.stalls_mem_any",
            "l1d_pend_miss.pending",
            "l1d_pend_miss.fb_full",
            "l1d_pend_miss.pending_cycles",
            "l1d_pend_miss.pending_cycles_any"
        ]

        ratios = dict()
        ratios['средняя доля промахов'] = np.mean(np.array(perfs['cache-misses']) / np.array(perfs['cache-references']))
        ratios['средняя доля промахов в L2'] = np.mean(np.array(perfs['l2_rqsts.all_demand_miss']) / np.array(perfs['l2_rqsts.all_demand_references']))
                                  
        perfs_ = dict()
        for param in params:
            perfs_[param], _ = stats(perfs[param])
        perfs = perfs_                                        

        for key in list(perfs.keys()):
            if key[-2:] in ['ди', 'ci']:
                del perfs_[key]

        nprs_mean, nprs_ci = stats(nprs)

        result.append({'name' : name} | top | perfs | ratios | {'nprs_mean' : nprs_mean, 'nprs_ci' : nprs_ci})

        curr_shift += 2 + 2 * N

    return pd.DataFrame(result)

if __name__ == '__main__':

    dfs = []

    for filename in os.listdir(sys.argv[1]):
        dfs.append(run(os.path.join(sys.argv[1], filename)))

    df = pd.concat(dfs, axis=0).reset_index()
    del df['index']

    print(df)
    print(list(df))

    df.to_csv(os.path.join(sys.argv[1], 'table.csv'))