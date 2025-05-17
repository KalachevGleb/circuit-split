import matplotlib.pyplot as plt
import numpy as np

FONT_SIZE = 18
plt.rcParams.update({'font.size': FONT_SIZE})

# Данные для Bitonic графа
# Формат: [depth значения для ядер 1-6, stock значения для всех размеров]
bitonic_data = {
    "8": {
        "depth": [0.623826, 1.306902, 1.953800, 2.488115, 8.550201, 9.354062],
        "stock": [0.516964, 0.516964, 0.516964, 0.516964, 0.516964, 0.516964]
    },
    "11": {
        "depth": [0.421174, 0.367805, 0.665951, 0.528458, 0.995287, 1.199816],
        "stock": [0.313235, 0.313235, 0.313235, 0.313235, 0.313235, 0.313235]
    },
    "15": {
        "depth": [2.161421, 1.475341, 1.705919, 1.674630, 1.285055, 1.950976],
        "stock": [1.716953, 1.716953, 1.716953, 1.716953, 1.716953, 1.716953]
    }
}

# Данные для Simple графа
simple_data = {
    "depth": [1.7256678, 1.0473674, 1.0443712, 0.7955647, 0.7976825, 0.7981431],
    "stock": [1.6668664, 1.0218823, 1.0442027, 0.7860621, 0.7952568, 0.7971633]
}

# Количество ядер
cores = [1, 2, 3, 4, 5, 6]
markers = ['o', 's', '^', 'D', 'v', '<']
colors = {
    '8': 'blue',
    '11': 'green',
    '15': 'red',
    'simple': 'purple'
}
linestyles = {
    'depth': '-',
    'stock': '--'
}

def plot_absolute_times():
    """Построение графика абсолютных времен выполнения"""
    plt.figure()
    
    # Две подграфика: для Bitonic и Simple графов
    fig, ax = plt.subplots(1, 1, figsize=(13, 8))

    # График для Simple-графа
    ax.plot(cores, simple_data["depth"], marker='o', color=colors["simple"], 
             linestyle=linestyles["depth"], label='Послойное')
    ax.plot(cores, simple_data["stock"], marker='x', color=colors["simple"], 
             linestyle=linestyles["stock"], label='Простое')
    
    ax.set_title('Время чтения для сдвинутого-графа', fontsize=FONT_SIZE)
    ax.set_xlabel('Количество ядер', fontsize=FONT_SIZE)
    ax.set_ylabel('Время чтения (нс)', fontsize=FONT_SIZE)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(fontsize=FONT_SIZE)
    
    plt.tight_layout()
    plt.savefig('absolute_time_simple.png', dpi=300)
    plt.close()

def plot_ratio():
    """Построение графика отношения depth/stock"""
    plt.figure()
    
    # Две подграфика: для Bitonic и Simple графов
    fig, ax = plt.subplots(1, 1, figsize=(13, 8))
    
    # График для Bitonic-графа
    for size in bitonic_data:
        # Расчет отношения stock/depth
        ratio = [s / d for s, d in zip(bitonic_data[size]["stock"], bitonic_data[size]["depth"])]
        ax.plot(cores, ratio, marker='o', color=colors[size], label=f'Битонический граф ширины {size}')
    
    # Горизонтальная линия на уровне 1 (stock = depth)
    ax.axhline(y=1, color='k', linestyle='--', alpha=0.5)

    ax.set_title('Отношение времени на чтение для однопоточного/послойного расписания', fontsize=FONT_SIZE)
    ax.set_xlabel('Количество ядер', fontsize=FONT_SIZE)
    ax.set_ylabel('Отношение', fontsize=FONT_SIZE)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(fontsize=FONT_SIZE)

    plt.tight_layout()
    plt.savefig('ratio_bitonic.png', dpi=300)
    plt.close()

def main():
    """Основная функция для генерации всех графиков"""
    print("Генерация графиков...")
    
    # Генерация отдельных графиков
    plot_absolute_times()
    plot_ratio()
    
    print("Все графики успешно сохранены!")

if __name__ == "__main__":
    main()
