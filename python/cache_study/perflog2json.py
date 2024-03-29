import sys
import string
import json
import os

def remove_spaces(s):
    ret = ''

    for d in s:
        if d in string.whitespace or d == ' ':
            continue

        ret = ret + d

    return ret

def first_digits(s):
    ret = ""

    for d in s:
        if d not in list(map(str, range(10))):
            break

        ret = ret + d

    return ret

def main():
    filelist = [os.path.join('blob', str(i) + '.perflog') for i in [2 ** j for j in range(13)]] + \
        [os.path.join('blob', 'stock.perflog')]
    
    res = dict()

    for path in filelist:
        with open(path, 'r') as fd:
            data = fd.read().split('\n')
        
        misses = [int(first_digits(remove_spaces(line))) for line in data if 'cache-misses' in line]
        refs = [int(first_digits(remove_spaces(line))) for line in data if 'cache-references' in line]

        name = os.path.basename(path).split('.')[0]
        res[name] = {
            'cache-misses' : misses,
            'cache-references' : refs
        }

    with open('blob/perf.json', 'w') as fd:
        json.dump(res, fd, indent=4, separators=(',', ': '))

if __name__ == '__main__':
    main()