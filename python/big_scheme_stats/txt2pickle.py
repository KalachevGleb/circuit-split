import json
import pickle
import sys

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

with open('log.pickle', 'wb') as fd:
    pickle.dump(objects, fd)