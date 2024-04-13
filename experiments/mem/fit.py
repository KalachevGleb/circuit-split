import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Загрузка данных из файла CSV
data = pd.read_csv('dataset.csv', header=None)

# Разделение данных на признаки (X) и целевую переменную (y)
X = data.iloc[:, :2]  # Признаки
y = data.iloc[:, 2]   # Целевая переменная

# Нормировка признаков и целевых значений
scaler = MinMaxScaler(feature_range=(-1, 1))
X_normalized = scaler.fit_transform(X)
y_normalized = scaler.fit_transform(y.values.reshape(-1, 1)).flatten()

# Разделение нормированных данных на обучающий и тестовый наборы
X_train, X_test, y_train, y_test = train_test_split(X_normalized, y_normalized, test_size=0.2, random_state=42)

# Обучение линейной регрессии
model = LinearRegression()
model.fit(X_train, y_train)

# Предсказание на тестовом наборе
y_pred = model.predict(X_test)

# Вычисление среднеквадратичной ошибки
mae = mean_absolute_error(y_test, y_pred)
print('Mean Absolute Error:', mae)

# Создание случайных предсказаний для сравнения
y_random = np.random.randn(len(y_test))  # Генерация случайных значений из нормального распределения

# Вычисление среднеквадратичной ошибки случайных предсказаний
mae_random = mean_absolute_error(y_test, y_random)
print('Random Prediction Mean Absolute Error:', mae_random)