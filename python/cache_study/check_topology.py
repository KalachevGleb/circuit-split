import sys
import json

import tqdm

def main():
    with open('dep_graph-600K-new.json', 'r') as fd:
        edges = [(e[1], e[0]) for e in json.load(fd)['edges']]

    with open(sys.argv[1], 'r') as fd:
        order = [e[1] for e in json.load(fd)['schedule'][0]]

    inv = dict()
    for i in range(len(order)):
        inv[order[i]] = i

    for edge in tqdm.tqdm(edges):
        if inv[edge[0]] >= inv[edge[1]]:
            print('Bad schedule')
            quit()

    print('Good schedule')

if __name__ == '__main__':
    main()