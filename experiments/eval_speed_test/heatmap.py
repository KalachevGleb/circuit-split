import sys

import numpy as np

import matplotlib.pyplot as plt

def main():
    fd = open('log.txt', 'r')
    lines = fd.read()
    fd.close()

    lines = [line.strip() for line in lines.split('\n') if len(line) > 0]

    data = []
    for i in range(0, len(lines), 3):
        data.append({
            'thread' : int(lines[i].split()[1]),
            'losses' : " ".join(lines[i].split()[2:4]),
            'predicted' : float(lines[i + 1].split()[1]),
            'real' : float(lines[i + 2].split()[1])
        })

    LOSSES = sorted(list(set([exp['losses'] for exp in data])))
    THREADS = sorted(list(set([exp['thread'] for exp in data])))

    data_pred = np.empty((len(LOSSES), len(THREADS)))
    data_real = np.empty((len(LOSSES), len(THREADS)))

    for exp in data:
        data_pred[LOSSES.index(exp['losses']), THREADS.index(exp['thread'])] = exp['predicted']
        data_real[LOSSES.index(exp['losses']), THREADS.index(exp['thread'])] = exp['real']

    print('Best real times:')
    print(str(np.amin(data_real, axis=0)) + 'ms')
    
    print('Min time:', np.amin(data_real))
    print('Max time:', np.amax(data_real))

    x = np.arange(len(THREADS))

    y1s = data_pred / np.max(data_pred, axis=1, keepdims=True)
    y2s = data_real / np.max(data_real, axis=1, keepdims=True)

    print(np.amin(np.sum(np.abs(y1s / y2s - 1), axis=1)) / len(THREADS))
    print(data[np.argmin(np.sum(np.abs(y1s / y2s - 1), axis=1))])


    width = 0.35

    fig, axs = plt.subplots(len(LOSSES), 1, figsize=(10, int(sys.argv[1])))

    for plot_num in range(len(axs)):
        ax = axs[plot_num]

        ax.bar(np.array([i + 1 for i in range(len(x))]) - width / 2, y1s[plot_num], width=width, label='predicted', color='green')
        ax.bar(np.array([i + 1 for i in range(len(x))]) + width / 2, y2s[plot_num], width=width, label='real', color='red')

        ax.set_xticks([i + 1 for i in range(len(x))])
        ax.set_xticklabels(list(map(int, THREADS)))
        
        ax.set_xlabel('threads')
        ax.set_ylabel('time')
        ax.set_title('LOSS=' + str(LOSSES[plot_num]))

        ax.legend()
    
    fig.suptitle('Нормированная производительность в зависимости от LOSS')

    plt.legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    plt.savefig('perfomance.png')

    plt.clf()

if __name__ == '__main__':
    main()