import json
import pickle

objects = []
with open('log.txt', 'r') as fd:
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