import numpy as np

import pandas as pd

from scipy.optimize import minimize

raw_col_num = len(pd.read_csv('dataset.csv', nrows=0).columns)

colnames = list(map(str, range(raw_col_num)))
colnames[0] = 'filename'
colnames[-2] = 'ns_per_node'

df = pd.read_csv('dataset.csv', names=colnames, dtype={'filename' : str, 'ns_per_node' : float})
df = df.loc[:, ['filename', 'ns_per_node']]

df['layers'] = df['filename'].apply(lambda x: eval(x.split('_')[-3]))
df['sizes'] = df['filename'].apply(lambda x: eval(x.split('_')[-2]))
del df['filename']

data = df.to_numpy(dtype=object)

def gen_dataset(data):
    simple = dict()
    multi = dict()
    for entry in data:
        if len(entry[1]) == 2:
            simple.update(
                {entry[1][1] : entry}
            )
        elif len(entry[1]) == 3:
            multi.update(
                {entry[1][1] : entry}
            )

    return simple, multi

simple_train, multi_train = gen_dataset(data[:129])
simple_test, multi_test = gen_dataset(data[129:])

print(len(multi_train))
print(len(multi_test))

def loss(x, simple, multi):
    x = np.array(x)

    val = []
    for num in multi:
        if simple[num][2][1] != multi[num][2][1] or simple[num+1][2][1] != multi[num][2][2]:
            print('Error')
            quit(1)

        A = npn_connected = multi[num][0] #ns_per_node

        sz_0, sz_1, sz_2 = multi[num][2][0], multi[num][2][1], multi[num][2][2]
        npn_1, npn_2 = simple[num][0], simple[num+1][0]
        vec = np.array([sz_0, sz_1, sz_2, npn_1, npn_2, 1])
        B = (sz_0 + sz_1 + sz_2) / ((sz_0 + sz_1) / npn_1 + (sz_1 + sz_2) / npn_2) + sz_0 * x[0] + sz_1 * x[1] + sz_2 * x[2] # + np.sum(x[:6] * vec)) + np.sum(x[6:] * vec)
        val.append(np.abs(B / A - 1))

    return np.mean(val)

def f1(x):
    return loss(x, simple_train, multi_train)

def f2(x):
    return loss(x, simple_test, multi_test)

res = minimize(f1, x0=[0] * 12, method='L-BFGS-B')

print(res.x)

print(f1(res.x))
print(f1([0] * 12))

print(f2(res.x))
print(f2([0] * 12))