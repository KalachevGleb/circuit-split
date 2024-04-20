import json

import numpy as np
from tqdm import tqdm

from sklearn import linear_model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MaxAbsScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

import pandas as pd

from matplotlib import pyplot as plt

PLOT = False

data = pd.read_csv('dataset.csv').to_numpy()
data = data[data[:, -2] < 0.5]

print('В датасете осталось объектов:', data.shape[0])

X = data[:, 1:-3]
y = data[:, -2]    

def main(aplha, l1_ratio):
    global X_train, X_test, y_train, y_test

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)

    regr = linear_model.ElasticNet(alpha=alpha, l1_ratio=l1_ratio)

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

if __name__ == '__main__':
    TEST_ROLLOUT_SIZE = 1000
    LISNSPACE_POINT_COUNT = 50

    result = []
    for alpha in tqdm(np.linspace(0, 10, LISNSPACE_POINT_COUNT)):
        for l1_ratio in tqdm(np.linspace(0, 1, LISNSPACE_POINT_COUNT)):
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)

            p = []
            for i in range(100):
                p.append(main(aplha=alpha, l1_ratio=l1_ratio))
            p = np.mean(p)

            result.append({
                'alpha' : alpha,
                'l1_ratio' : l1_ratio,
                'MPE' : p
            })

    with open('linear_elastic_net_rollout.json', 'w') as fd:
        json.dump(result, fd, indent=2)

    result.sort(key=lambda experiment: 500 if experiment['MPE'] is None else experiment['MPE'])
    for exp in result[:5]:
        ps = []
        for i in tqdm(range(TEST_ROLLOUT_SIZE)):
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)
            ps.append(main(exp['alpha'], exp['l1_ratio']))

        print()
        print('Предсказанная средняя MPE:', exp['MPE'])
        print('Реальная средняя MPE:', np.mean(ps))
        print('Максимальная MPE', np.amax(ps))
