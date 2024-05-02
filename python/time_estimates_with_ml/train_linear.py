import sys

import json

import numpy as np
from tqdm import tqdm

from sklearn import linear_model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MaxAbsScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import KFold

import pandas as pd

from matplotlib import pyplot as plt

import warnings
warnings.filterwarnings("ignore")

PLOT = False
df = pd.read_csv('dataset.csv', dtype=str)
numeric_df = df.apply(pd.to_numeric, errors='coerce')
data = numeric_df[numeric_df.notna().all(axis=1)].to_numpy()
data = data[data[:, -2] > float(sys.argv[1]), :]
data = data[data[:, -2] < float(sys.argv[2]), :]

print('В датасете осталось объектов:', data.shape[0])

X = data[:, 1:-3]
y = data[:, -2]

def train(X_train, X_test, y_train, y_test, model=linear_model.LinearRegression()):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)

    regr = model
    regr.fit(X_train, y_train)

    y_pred = regr.predict(scaler.transform(X_test))

    # print('MAE:', round(mean_absolute_error(y_test, y_pred), 3))
    # print('MSE:', round(mean_squared_error(y_test, y_pred), 3))
    # print('std:', round(np.std(y_test - y_pred), 3))
    mpe = np.mean(np.abs(y_pred / y_test - 1) * 100)
    # print('Средняя ошибка:', str(round(mpe, 3)) + '%')

    # print()
    # print('Коэффициенты регрессии:')
    # print('Однопоточная стоимость:', round(regr.coef_[0], 3))
    # print('Барьеров:', round(regr.coef_[1],3))
    # print('Чтений в одном потоке:', round(regr.coef_[2], 3), round(regr.coef_[3], 3))
    # print('Чтений между потоками:', round(regr.coef_[4], 3), round(regr.coef_[5], 3))
    # print('Записей:', round(regr.coef_[6], 3), round(regr.coef_[7], 3))

    if PLOT:
        plt.plot(list(range(len(y_pred))), y_pred, label='pred')
        plt.plot(list(range(len(y_test))), y_test, label='real')
        plt.legend()
        plt.savefig('plot.png')

    return mpe

def finetune_elastic():
    global X, y

    KFOLD_N = 10
    LISNSPACE_POINT_COUNT = 10

    result = []
    for alpha in tqdm(np.linspace(0, 10, LISNSPACE_POINT_COUNT)):
        for l1_ratio in tqdm(np.linspace(0, 1, LISNSPACE_POINT_COUNT)):
            kf = KFold(n_splits=KFOLD_N, random_state=None, shuffle=True)
            train_results = []
            for train1, test1 in kf.split(X):
                train_results.append(train(X[train1], X[test1], y[train1], y[test1],
                         linear_model.ElasticNet(alpha=alpha, l1_ratio=l1_ratio)))

            result.append({
                'alpha' : alpha,
                'l1_ratio' : l1_ratio,
                'MPE' : np.mean(train_results)
            })

    with open('linear_elastic_net_rollout.json', 'w') as fd:
        json.dump(result, fd, indent=2)

    result.sort(key=lambda experiment: 1e10 if experiment['MPE'] is None else experiment['MPE'])
    print(json.dumps(result[:10], indent=2))

if __name__ == '__main__':
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)

    train(X_train, X_test, y_train, y_test)

    finetune_elastic()