import os
import json
import re
import random

NS_PER_NODE_1T = 0.681875

def remove_duplicates_except_last(lst, key=lambda x: x):
    seen = {}
    result = []
    for item in reversed(lst):
        k = key(item)
        if k not in seen:
            result.append(item)
            seen[k] = True
    return list(reversed(result))

def merge_dicts(list1, list2):
    result = []
    dict_map = {}
    
    # Create a mapping of 'threads' values to dictionaries from list2
    for item in list2:
        key = (item['threads'], item['LOSS1'], item['LOSS2'])
        dict_map[key] = item
    
    # Merge dictionaries from list1 and list2
    for item in list1:
        key = (item['threads'], item['LOSS1'], item['LOSS2'])
        if key in dict_map:
            merged_dict = {**item, **dict_map[key]}
            result.append(merged_dict)
    
    return result

def main():

    #
    # Обрабатываем csv
    #

    with open('rollout.csv', 'r') as fd:
        data_A = [line.split(',') for line in fd.readlines()]

    data_A = [{
        'threads' : int(e[0]),
        'LOSS1' : int(e[1]),
        'LOSS2' : int(e[2]),
        'cost1' : float(e[3]),
        'costn' : [float(c) for c in e[4:]]
    } for e in data_A]

    data_A = remove_duplicates_except_last(data_A, lambda x: (x['threads'], x['LOSS1'], x['LOSS2']))

    #
    # Обрабатываем json
    #

    data_B = []
    for folder in os.listdir('rollouts'):
        path = os.path.join('rollouts', folder)
        if not os.path.isdir(path):
            continue
        if not folder.isdigit():
            continue

        for file in os.listdir(path):
            fpath = os.path.join(path, file)
            
            with open(fpath, 'r') as fd:
                entry = json.load(fd)

                LOSS1, LOSS2 = list(map(int, re.findall(r'\d+', file)))
                entry['LOSS1'] = LOSS1
                entry['LOSS2'] = LOSS2
                entry['threads'] = int(folder)

                data_B.append(entry)

    #
    # join и дамп
    #

    data = merge_dicts(data_A, data_B)

    print('Пример эксперимента:')
    print(json.dumps(random.choice(data), indent=4))
    print('Всего экспериментов:', len(data))

    threads = sorted(list(set([e['threads'] for e in data])))

    with open('rollout.json', 'w') as fd:
        json.dump({
            'threads' : threads,
            'results' : data
        }, fd, indent=4)

    #
    # Ищем LOSS'ы для самого точного предсказания
    #

    for i in range(len(data)):
        data[i]['ratio_predicted'] = max(data[i]['costn']) / data[i]['cost1']
        data[i]['ratio_real'] = data[i]['ns_per_node'] / NS_PER_NODE_1T
        data[i]['ratio'] = data[i]['ratio_predicted'] / data[i]['ratio_real']

    data = sorted(data, key=lambda e: abs(1 - e['ratio']))
    for e in data[:10]:
        print()
        print(json.dumps(e, indent=4))

if __name__ == '__main__':
    main()