import matplotlib.pyplot as plt
import numpy as np

# Глобальная переменная для размера шрифта
FONT_SIZE = 16

# Применяем размер шрифта ко всем элементам через rcParams
plt.rcParams.update({'font.size': FONT_SIZE})

# Захардкоженные данные
yandex_simple = {
    "stock": [2.4787647, 1.1623689, 0.79653409, 0.6353147, 0.82843513, 0.7165782],
    "depth": [2.304854, 1.1995959, 0.84259054, 0.69629675, 0.90904695, 0.78361534]
}

# Создаем индексы для оси X
x = np.arange(len(yandex_simple["stock"]))
labels = list(range(1, len(yandex_simple["stock"])+1))

# Настраиваем фигуру
plt.figure(figsize=(10, 6))

# Строим линии с маркерами
plt.plot(x, yandex_simple["stock"], 'o-', linewidth=2, markersize=8, label='Расписание, сделанное вручную', color='#FF0000')
plt.plot(x, yandex_simple["depth"], 's-', linewidth=2, markersize=8, label='Послойное расписание', color='#0000FF')

# Добавляем сетку для лучшей читаемости
plt.grid(True, linestyle='--', alpha=0.7)

# Устанавливаем подписи осей и заголовок
plt.xlabel('Число потоков', fontsize=FONT_SIZE)
plt.ylabel('Среднее время чтения (нс)', fontsize=FONT_SIZE)
plt.title(r'Сравнение сделанного вручную расписания и послойного на $SH(20, 17)$', fontsize=FONT_SIZE)

# Устанавливаем метки на оси X
plt.xticks(x, labels)

# Добавляем легенду
plt.legend(fontsize=FONT_SIZE)

# Добавляем числовые значения над точками (шрифт оставляем явным, не зависящим от FONT_SIZE)
for i, (stock_val, depth_val) in enumerate(zip(yandex_simple["stock"], yandex_simple["depth"])):
    plt.annotate(f'{stock_val:.2f}', 
                 (i, stock_val), 
                 textcoords="offset points", 
                 xytext=(0, 10), 
                 ha='center',
                 fontsize=9,
                 color='#FF0000')
    plt.annotate(f'{depth_val:.2f}', 
                 (i, depth_val), 
                 textcoords="offset points", 
                 xytext=(0, -15), 
                 ha='center',
                 fontsize=9,
                 color='#0000FF')

# Устанавливаем границы по осям для лучшей наглядности
plt.ylim(0.5, 2.6)

# Добавляем область разницы между кривыми для наглядности
plt.fill_between(x, yandex_simple["stock"], yandex_simple["depth"], 
                 where=(np.array(yandex_simple["stock"]) > np.array(yandex_simple["depth"])),
                 interpolate=True, alpha=0.1, label='Stock > Depth', color='red')
plt.fill_between(x, yandex_simple["stock"], yandex_simple["depth"], 
                 where=(np.array(yandex_simple["stock"]) < np.array(yandex_simple["depth"])),
                 interpolate=True, alpha=0.1, label='Stock < Depth', color='blue')

# Плотная компоновка
plt.tight_layout()

plt.savefig('sh_thread_speedup.png')