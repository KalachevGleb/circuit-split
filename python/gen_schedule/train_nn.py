import os

import numpy as np

import keras
from keras import layers, initializers
from keras import ops

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MaxAbsScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

from matplotlib import pyplot as plt

import pandas as pd

SIGMA = 0.001
LR = 0.00001
BATCH_SIZE = 32
EPOCHS = 10000
DROPOUT_RATE = 0.7

data = pd.read_csv('dataset.csv').to_numpy()
data = data[data[:, -2] < 1]

print('В датасете осталось объектов:', data.shape[0])

X = data[:, 1:-3]
y = data[:, -2]
data_dim = X.shape[1]

print('Используется признаков:', data_dim)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

model = keras.Sequential(
    [
        layers.Dense(data_dim, activation="linear", name="layer1", kernel_initializer=initializers.RandomNormal(stddev=SIGMA)),
        layers.BatchNormalization(),
        layers.Activation(activation='relu'),
        layers.Dropout(rate=DROPOUT_RATE),
        layers.Dense(data_dim // 3, activation="linear", name="layer2", kernel_initializer=initializers.RandomNormal(stddev=SIGMA)),
        layers.BatchNormalization(),
        layers.Activation(activation='relu'),
        layers.Dropout(rate=DROPOUT_RATE),
        layers.Dense(1, activation='linear', name="layer3", kernel_initializer=initializers.RandomNormal(stddev=SIGMA)),
    ]
)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=LR),
    loss=keras.losses.MeanAbsoluteError(),
    metrics=[keras.metrics.MeanAbsoluteError(), keras.metrics.MeanSquaredError()],
)

history = model.fit(
    X_train,
    y_train,
    batch_size=BATCH_SIZE,
    epochs=EPOCHS,
    validation_data=(X_test, y_test),
)

y_pred = model.predict(X_test)

print('MAE:', round(mean_absolute_error(y_test, y_pred), 3))
print('MSE:', round(mean_squared_error(y_test, y_pred), 3))
print('std:', round(np.std(y_test - y_pred), 3))
print('Средняя ошибка:', str(round(np.mean(np.abs(y_pred / y_test - 1) * 100), 3)) + '%')

if not os.path.exists('plots'):
    os.mkdir('plots')
plot_num = len(os.listdir('plots')) + 1

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.savefig(os.path.join('plots', str(plot_num) + '.png'))

