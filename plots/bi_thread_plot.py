import matplotlib.pyplot as plt
import numpy as np

# Global font size for all text elements (excluding annotations)
FONT_SIZE = 16
plt.rcParams.update({'font.size': FONT_SIZE})

# Словарь с данными
yandex_bitonic = {
    "8": {
        "th_1_depth": 2.2471469,
        "th_2_depth": 2.4192981,
        "th_3_depth": 2.6680006,
        "th_4_depth": 3.4142355,
        "th_5_depth": 4.0432908,
        "th_6_depth": 4.6008615,
    },
    "11": {
        "th_1_depth": 1.55419721,
        "th_2_depth": 1.46194391,
        "th_3_depth": 0.52049259,
        "th_4_depth": 0.53659801,
        "th_5_depth": 0.60491530,
        "th_6_depth": 0.63095934,
    },
    "15": {
        "th_1_depth": 2.2595929,
        "th_2_depth": 1.2458149,
        "th_3_depth": 0.87683264,
        "th_4_depth": 0.71151138,
        "th_5_depth": 0.92873474,
        "th_6_depth": 0.81211889,
    },
    "stock": {
        "8_stock": 1.3721976,
        "11_stock": 0.55354684,
        "15_stock": 1.9851819,
    },
}

# Настройка стиля
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(12, 8))

# Глубины для оси X
depths = ["th_1_depth", "th_2_depth", "th_3_depth", "th_4_depth", "th_5_depth", "th_6_depth"]
x_labels = ["1", "2", "3", "4", "5", "6"]  # Метки для оси X
x_pos = np.arange(len(depths))

# Категории и их цвета
categories = ["8", "11", "15"] 
labels = [r"Послойное $BI(8)$", r"Послойное $BI(11)$", r"Послойное $BI(15)$"]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Разные цвета для каждой категории
markers = ['o', 's', '^']  # Разные маркеры для каждой категории
lines = []

# Построение линий для каждой категории
for i, category in enumerate(categories):
    values = [yandex_bitonic[category][depth] for depth in depths]
    line, = ax.plot(x_pos, values, marker=markers[i], linewidth=2.5, color=colors[i], 
                   markersize=10, label=labels[i])
    lines.append(line)
    
    # Добавление значений на график (аннотации оставляем с фиксированным размером)
    for j, val in enumerate(values):
        ax.annotate(f'{val:.2f}', 
                    xy=(x_pos[j], val), 
                    xytext=(0, 7 if i == 0 else (-15 if i == 1 else 15)),
                    textcoords='offset points',
                    ha='center', 
                    fontsize=9,
                    color=colors[i],
                    fontweight='bold')
    
    stock_value = yandex_bitonic["stock"][f"{category}_stock"]
    ax.axhline(y=stock_value, color=colors[i], linestyle='--', linewidth=1.5, alpha=0.6, label=r'Ручное однопоточное $BI(' + str(category) + r")$" + f': {stock_value:.2f}')
# Настройка осей без явного указания fontsize (будет использован FONT_SIZE)
ax.set_xlabel('Число потоков')
ax.set_ylabel('Среднее время чтения (нс)')
ax.set_title(r'Сравнение сделанного вручную расписания и послойного на $BI(8),BI(11)$ и $BI(15)$')
ax.set_xticks(x_pos)
ax.set_xticklabels(x_labels)
ax.grid(True, linestyle='--', alpha=0.7)

# Легенда
ax.legend(loc='upper left')

# Настройка границ и стиля осей
ax.set_xlim(-0.2, len(depths) - 0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()

plt.savefig('bi_thread_speedup.png')
