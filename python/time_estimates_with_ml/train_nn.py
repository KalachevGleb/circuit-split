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

import torch

from tqdm.keras import TqdmCallback

USE_CUDA = torch.cuda.is_available()
print('Cuda status:', torch.cuda.is_available())
if USE_CUDA:
    device = torch.device('cuda')
else:
    device = torch.device('cpu') 

parser = argparse.ArgumentParser(description='Videos to images')
parser.add_argument('--sigma', type=float, default=0.05)
parser.add_argument('--lr', type=float, default=0.001)
parser.add_argument('--batch_size', type=int, default=64)
parser.add_argument('--epochs', type=int, default=10000)
parser.add_argument('--dropout_rate', type=float, default=0.4)
parser.add_argument('--th_y_high', type=float, default=10)
parser.add_argument('--th_y_low', type=float, default=1)
parser.add_argument('--loss_shape', type=str, default='mse')
parser.add_argument('--load_chkp', type=str, default='<none>')
parser.add_argument('--activation', type=str, default='relu')
args = parser.parse_args()

SIGMA = args.sigma
LR = args.lr
BATCH_SIZE = args.batch_size
EPOCHS = args.epochs
DROPOUT_RATE = args.dropout_rate
TH_Y_HIGH = args.th_y_high
TH_Y_LOW = args.th_y_low
LOSS_SHAPE = args.loss_shape
START_CHKP = args.load_chkp
ACTIVATION = args.activation


df = pd.read_csv('dataset.csv', dtype=str)
numeric_df = df.apply(pd.to_numeric, errors='coerce')
data = numeric_df[numeric_df.notna().all(axis=1)].to_numpy()
data = data[data[:, -2] < TH_Y_HIGH]
data = data[data[:, -2] > TH_Y_LOW]


print('В датасете осталось объектов:', data.shape[0])

X = data[:, 1:-3]
y = data[:, -2]
data_dim = X.shape[1]

print('Используется признаков:', data_dim)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

y_min, y_max = np.amax(y_train), np.amin(y_train)
def normalize_y(y):
    global y_min, y_max
    return np.tanh(((y - y_min) / (y_max - y_min) - 0.5) * 2)
def reset_y(y):
    global y_min, y_max
    return ((np.arctanh(y) / 2) + 0.5) * (y_max - y_min) + y_min

with torch.cuda.device(device):
    losses = {'mse' : keras.losses.MeanSquaredError(),
            'mae' : keras.losses.MeanAbsoluteError(),
            'per' : keras.losses.MeanAbsolutePercentageError()
    }
    metrics = {
        'mse' : keras.metrics.MeanSquaredError(),
        'mae' : keras.metrics.MeanAbsoluteError(),
        'per' : keras.metrics.MeanAbsolutePercentageError()
    }

    if START_CHKP == '<none>':
        model = keras.Sequential(
            [
                layers.Dense(data_dim, activation=ACTIVATION, name="layer1", kernel_initializer=initializers.RandomNormal(stddev=SIGMA)),
                layers.BatchNormalization(),
                layers.Dropout(rate=DROPOUT_RATE),
                layers.Dense(data_dim, activation=ACTIVATION, name="layer2",kernel_initializer=initializers.RandomNormal(stddev=SIGMA)),
                layers.BatchNormalization(),
                layers.Dropout(rate=DROPOUT_RATE),
                layers.Dense(1, activation='linear', name="layer3", kernel_initializer=initializers.RandomNormal(stddev=SIGMA)),
            ]
        )

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=LR),
            loss=losses[LOSS_SHAPE],
            metrics=[metrics[LOSS_SHAPE]],
        )
    else:
        model = keras.saving.load_model(START_CHKP)

    history = model.fit(
        X_train,
        normalize_y(y_train),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        validation_data=(X_test, y_test),
        verbose=0,
        callbacks=[TqdmCallback(verbose=1)]
    )

    y_pred = reset_y(model.predict(X_test))

print('MAE:', round(mean_absolute_error(y_test, y_pred), 3))
print('MSE:', round(mean_squared_error(y_test, y_pred), 3))
print('std:', round(np.std(y_test - y_pred), 3))
mean_percentage_error = np.mean(np.abs(y_pred / y_test - 1) * 100)
print('Средняя ошибка:', str(round(mean_percentage_error, 3)) + '%')

token = secrets.token_hex(nbytes=4)

if not os.path.exists('plots'):
    os.mkdir('plots')
plot_num = len(os.listdir('plots')) + 1

plt.plot(history.history[losses[LOSS_SHAPE].name], color='red', label='train_loss')
plt.plot(history.history['val_' + losses[LOSS_SHAPE].name], color='green', label='val_loss')
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(loc='upper right')
plt.savefig(os.path.join('plots', str(plot_num) + '_' + token + '.png'))

if not os.path.exists('nns'):
    os.mkdir('nns')
shutil.copy(sys.argv[0], os.path.join('nns', str(plot_num) + '_' + token + '_MPE=' + str(round(mean_percentage_error, 3)) + '.py'))
hyperparameters = {'SIGMA' : SIGMA,
                   'LR' : LR,
                   'BATCH_SIZE' : BATCH_SIZE,
                   'EPOCHS' : EPOCHS,
                   'DROPOUT_RATE' : DROPOUT_RATE,
                   'TH_Y_HIGH' : TH_Y_HIGH,
                   'TH_Y_LOW' : TH_Y_LOW,
                   'LOSS_SHAPE' : LOSS_SHAPE,
                   'START_CHKP' : START_CHKP,
                   'ACTIVATION' : ACTIVATION,
                   'time' : time.time()
                  }
with open(os.path.join('nns', str(plot_num) + '_' + token + '.json'), 'w') as fd:
    json.dump(hyperparameters, fd)

model.save(os.path.join('nns', str(plot_num) + '_' + token + '.keras'))

print('Записано:', str(plot_num) + '_' + token)