#!/bin/bash

mkdir -p rollouts

for scheme in rollout_graphs/*; do
    for threads in 2 3 4 5 6 7 8; do
        name=$(basename ${scheme} .json)

        if test -f "rollouts/${name}_${threads}.txt"; then
            continue
        fi
        
        output=$(python gen.py ${threads} 1 0 ${scheme} cut.json)

        single_thread_cost=$(echo "$output" | grep -oE 'Стоимость однопоточного вычисления: ([0-9]+\.*)' | awk '{print $NF}')
        barriers=$(echo "$output" | grep -oE 'Барьеров: ([0-9]+\.*)' | awk '{print $NF}')
        util=$(echo "$output" | grep -oE 'Утилизация потоков: ([0-9]+\.[0-9]+*)' | awk '{print $NF}')
        #cost=$(echo "$output" | grep -oE '[0-9]+\.[0-9]+' | awk 'NR<=2 {printf "%s%s", $1, (NR<2 ? "," : "\n")}')

        echo "$name, $threads, $single_thread_cost, $barriers, $util"  >> rollout.csv
        
        rm -rf blob
        simulation cut.json blob/work/ --compiler /usr/bin/clang++ --run --time 10 > "rollouts/${name}_${threads}.txt"
    done
done