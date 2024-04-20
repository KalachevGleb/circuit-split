import pandas as pd
from sklearn import linear_model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MaxAbsScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

from matplotlib import pyplot as plt

data = pd.read_csv('dataset.csv').to_numpy()
data = data[data[:, -2] < 0.5]

print('В датасете осталось объектов:', data.shape[0])

X = data[:, 1:-3]
y = data[:, -2]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)

regr = linear_model.LinearRegression()

regr.fit(X_train, y_train)

y_pred = regr.predict(scaler.transform(X_test))

print('MAE:', round(mean_absolute_error(y_test, y_pred), 3))
print('MSE:', round(mean_squared_error(y_test, y_pred), 3))
print('std:', round(np.std(y_test - y_pred), 3))
print('Средняя ошибка:', str(round(np.mean(np.abs(y_pred / y_test - 1) * 100), 3)) + '%')

plt.plot(list(range(len(y_pred))), y_pred, label='pred')
plt.plot(list(range(len(y_test))), y_test, label='real')
plt.legend()
plt.savefig('plot.png')