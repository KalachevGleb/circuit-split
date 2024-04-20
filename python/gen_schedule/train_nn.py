import os
import shutil
import sys
import json
import argparse
import time
import secrets

import numpy as np

import keras
from keras import layers, initializers
from keras import ops

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MaxAbsScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

from matplotlib import pyplot as plt

import pandas as pd

parser = argparse.ArgumentParser(description='Videos to images')
parser.add_argument('--sigma', type=float, default=0.001)
parser.add_argument('--lr', type=float, default=0.00001)
parser.add_argument('--batch_size', type=float, default=32)
parser.add_argument('--epochs', type=int, default=10000)
parser.add_argument('--dropout_rate', type=float, default=0.7)
args = parser.parse_args()

SIGMA = args.sigma
LR = args.lr
BATCH_SIZE = args.batch_size
EPOCHS = args.epochs
DROPOUT_RATE = args.dropout_rate

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
        layers.Dense(data_dim // 3, activation="linear", name="layer1", kernel_initializer=initializers.RandomNormal(stddev=SIGMA)),
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
mean_percentage_error = np.mean(np.abs(y_pred / y_test - 1) * 100)
print('Средняя ошибка:', str(round(mean_percentage_error, 3)) + '%')

token = secrets.token_hex(nbytes=4)

if not os.path.exists('plots'):
    os.mkdir('plots')
plot_num = len(os.listdir('plots')) + 1

plt.plot(history.history['mean_absolute_error'])
plt.plot(history.history['val_mean_absolute_error'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.savefig(os.path.join('plots', str(plot_num) + '_' + token + '.png'))

if not os.path.exists('nns'):
    os.mkdir('nns')
shutil.copy(sys.argv[0], os.path.join('nns', str(plot_num) + '_' + token + '_MPE=' + str(round(mean_percentage_error, 3)) + '.py'))
hyperparameters = {'SIGMA' : SIGMA,
                   'LR' : LR,
                   'BATCH_SIZE' : BATCH_SIZE,
                   'EPOCHS' : EPOCHS,
                   'DROPOUT_RATE' : DROPOUT_RATE,
                   'time' : time.time()
                  }
with open(os.path.join('nns', str(plot_num) + '_' + token + '.json'), 'w') as fd:
    json.dump(hyperparameters, fd)