import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# Размер шрифта для всего текста на графиках
FONT_SIZE = 18

# Настройка стиля графиков
plt.style.use('seaborn-v0_8-whitegrid')
# Размер фигуры и базовый размер шрифта
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = FONT_SIZE

# Единообразное применение размера шрифта ко всем элементам
plt.rcParams['axes.titlesize'] = FONT_SIZE
plt.rcParams['axes.labelsize'] = FONT_SIZE
plt.rcParams['xtick.labelsize'] = FONT_SIZE
plt.rcParams['ytick.labelsize'] = FONT_SIZE
plt.rcParams['legend.fontsize'] = FONT_SIZE

# Данные из таблиц
# Битонический граф 8
data_bitonic8 = {
    'cache_256': 0.5772591899999999,
    'cache_1024': 0.56468452,
    'cache_4096': 0.53199706,
    'cache_16384': 0.51522837,
    'cache_65536': 0.51714907,
    'stock': 0.54000828
}

# Битонический граф 11
data_bitonic11 = {
    'cache_256': 0.33173284000000003,
    'cache_1024': 0.32476573999999997,
    'cache_4096': 0.31791908,
    'cache_16384': 0.31171783999999997,
    'cache_65536': 0.25744216000000003,
    'cache_131072': 0.23574525000000002,
    'cache_262144': 0.23542284,
    'stock': 0.35476748999999996
}

# Битонический граф 15
data_bitonic15 = {
    'cache_256': 1.4300664,
    'cache_1024': 1.4682503,
    'cache_4096': 1.4372962,
    'cache_16384': 1.4333799999999999,
    'cache_65536': 1.4559358,
    'stock': 1.4907043
}

# Сдвинутый граф 131072_20
data_simple = {
    'cache_256': 1.8710235,
    'cache_1024': 1.8873027,
    'cache_4096': 1.8704468,
    'cache_16384': 1.884778,
    'cache_65536': 1.8722273999999999,
    'stock': 1.5863401
}

# Извлечение размеров кэша без префикса "cache_"
def extract_cache_sizes(data_dict):
    sizes = []
    values = []
    stock_value = data_dict['stock']
    for key, value in data_dict.items():
        if key != 'stock':
            size = int(key.split('_')[1])
            sizes.append(size)
            values.append(value)
    sizes, values = zip(*sorted(zip(sizes, values)))
    return sizes, values, stock_value

# Обработка данных для всех типов графов
sizes_bitonic8, values_bitonic8, stock_bitonic8 = extract_cache_sizes(data_bitonic8)
sizes_bitonic11, values_bitonic11, stock_bitonic11 = extract_cache_sizes(data_bitonic11)
sizes_bitonic15, values_bitonic15, stock_bitonic15 = extract_cache_sizes(data_bitonic15)
sizes_simple, values_simple, stock_simple = extract_cache_sizes(data_simple)

# Создание графика для относительного ускорения
plt.figure(figsize=(12, 8))
rel_speedup_bitonic8 = [stock_bitonic8/val for val in values_bitonic8]
rel_speedup_bitonic11 = [stock_bitonic11/val for val in values_bitonic11]
rel_speedup_bitonic15 = [stock_bitonic15/val for val in values_bitonic15]
rel_speedup_simple = [stock_simple/val for val in values_simple]

plt.plot(sizes_bitonic8, rel_speedup_bitonic8, 'o-', label='Битонический граф ширины 2^8', linewidth=2)
plt.plot(sizes_bitonic11, rel_speedup_bitonic11, 's-', label='Битонический граф ширины 2^11', linewidth=2)
plt.plot(sizes_bitonic15, rel_speedup_bitonic15, '^-', label='Битонический граф ширины 2^15', linewidth=2)
plt.plot(sizes_simple, rel_speedup_simple, 'D-', label='Сдвинутый граф', linewidth=2)

plt.axhline(y=1.0, linestyle='-', color='gray', alpha=0.7, label='Без ускорения (стандартная реализация)')
plt.xscale('log', base=2)
plt.grid(True, which="both", ls="-", alpha=0.2)
plt.xlabel('Размер кэша (байт)')
plt.ylabel('Множитель ускорения')
plt.title('Относительное ускорение за счет симуляции кэша')
plt.legend(loc='best')
plt.tight_layout()
plt.savefig('relative_speedup.png', dpi=300)

# Создание гистограммы для сравнения оптимальных случаев с базовыми
plt.figure(figsize=(12, 8))
optimal_bitonic8 = min(values_bitonic8)
optimal_bitonic11 = min(values_bitonic11)
optimal_bitonic15 = min(values_bitonic15)
optimal_simple = min(values_simple)

graph_types = ['Бит. граф ширины 2^8', 'Бит. граф ширины 2^11', 'Бит. граф ширины 2^15', 'Сдвинутый граф']
optimal_values = [optimal_bitonic8, optimal_bitonic11, optimal_bitonic15, optimal_simple]
stock_values = [stock_bitonic8, stock_bitonic11, stock_bitonic15, stock_simple]
x = np.arange(len(graph_types))
width = 0.35

fig, ax = plt.subplots(figsize=(14, 8))
rects1 = ax.bar(x - width/2, optimal_values, width, label='Оптимизированная версия (лучший кэш)')
rects2 = ax.bar(x + width/2, stock_values, width, label='Стандартная реализация')

for i in range(len(graph_types)):
    improvement = (stock_values[i] - optimal_values[i]) / stock_values[i] * 100
    ax.text(i, optimal_values[i]/2, f'{improvement:.1f}%', ha='center', va='center', fontsize=FONT_SIZE)

ax.set_ylabel('Время доступа (нс)')
ax.set_title('Сравнение оптимальных кэш-оптимизированных и стандартных расписаний')
ax.set_xticks(x)
ax.set_xticklabels(graph_types)
ax.legend()

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=FONT_SIZE)

autolabel(rects1)
autolabel(rects2)
fig.tight_layout()
plt.savefig('comparsion_histogram.png', dpi=300)

# Показать все графики
# plt.show()
