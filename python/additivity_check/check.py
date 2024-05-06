import numpy as np
from tqdm import tqdm
import pandas as pd

from scipy.optimize import minimize

I = 7

def load_dataset(filename):

    df = pd.read_csv(filename, dtype={'filename' : str, 
                                      'ns_per_node' : str,
                                      'vals1' : str,
                                      'vals2' : str,
                                      'vals3' : str
                                      })
    df = df.loc[:, ['filename', 'ns_per_node', 'vals1', 'vals2', 'vals3']]

    df['layers'] = df['filename'].apply(lambda x: eval(x.split('_')[-3]))
    df['sizes'] = df['filename'].apply(lambda x: eval(x.split('_')[-2]))
    del df['filename']

    df['ns_per_node'] = df['ns_per_node'].apply(lambda x: np.mean(eval(x)))

    df['vals1'] = df['vals1'].apply(lambda x: eval(x.split(':')[-1]))
    df['vals2'] = df['vals2'].apply(lambda x: eval(x.split(':')[-1]))
    df['vals3'] = df['vals3'].apply(lambda x: eval(x.split(':')[-1]))

    simple = dict()
    multi = dict()
    def line2dict(line):
        return {'sizes' : line['sizes'],
                'ns_per_node' : line['ns_per_node'],
                'vals1' : line['vals1'],
                'vals2' : line['vals2'],
                'vals3' : line['vals3']
                }
    
    skipped_multi = 0
    for index, line in df.iterrows():
        if len(line['layers']) == 2:
            simple.update({line['layers'][1] : line2dict(line)})
        elif len(line['layers']) == I and line['ns_per_node'] < 5:
            multi.update({line['layers'][1] : line2dict(line)})
        elif len(line['layers']) == I:
            skipped_multi += 1

    print('Пропущено', str(skipped_multi) + '/' + str(len(multi) + skipped_multi))

    return simple, multi

simple_train, multi_train = load_dataset('rollout_600k.csv')
simple_test, multi_test = load_dataset('rollout_dep_graph.csv')

print(len(multi_train))
print(len(multi_test))

buff = None

def loss(x, simple, multi):
    x = np.array(x)

    global buff
    buff = []
    val = []
    for num in multi:
        for i in range(I-1):
            if simple[num+i]['sizes'][1] != multi[num]['sizes'][i+1]:
                print('Error')
                quit(1)

        target = multi[num]['ns_per_node']
        
        vals1 = multi[num]['vals1']
        vals2 = multi[num]['vals2']
        vals3 = multi[num]['vals3']

        szs = np.array(multi[num]['sizes'])
        npns = np.array([simple[num+i]['ns_per_node'] for i in range(I-1)])
        
        predicted = np.sum(np.array(npns) * x[:6]) + x[6] + (np.sum(szs)) / np.sum([(szs[i] + szs[i+1]) / npns[i] for i in range(I-1)])
        val.append(np.abs(predicted - target))
        buff.append(np.abs(predicted / target - 1))
    
    buff = np.mean(buff)
    return np.mean(val)

def f1(x):
    return loss(x, simple_train, multi_train)

def f2(x):
    return loss(x, simple_test, multi_test)

scores_train, scores_test = [], []
for i in tqdm(range(20)):
    res = minimize(f1, x0=np.random.randn(13) * 0.01, method='L-BFGS-B')
    f1(res.x)
    scores_train.append(buff)
    f2(res.x)
    scores_test.append(buff)
print('Train:', scores_train[np.argmin(scores_test)])
print('Test:', np.amin(scores_test))