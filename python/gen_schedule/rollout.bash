#!/bin/bash

mkdir -p rollouts

losses=$(echo 1; seq 10 10 100; seq 200 100 1000; seq 2000 500 11000)

for threads in 2; do
    mkdir -p "rollouts/$threads"

    for LOSS1 in $losses; do
        for LOSS2 in $losses; do
            if test -f "rollouts/${threads}/${LOSS1}_${LOSS2}.txt"; then
                continue
            fi
            
            output=$(python gen.py 2 $LOSS1 $LOSS2  bitonic10.json cut.json)
            single_threaded_cost=$(echo "$output" | grep -oE 'Стоимость однопоточного вычисления: ([0-9]+\.*)' | awk '{print $NF}')
            cost=$(echo "$output" | grep -oE '[0-9]+\.[0-9]+' | awk 'NR<=2 {printf "%s%s", $1, (NR<2 ? "," : "\n")}')
            echo "$threads, $LOSS1, $LOSS2, $single_threaded_cost, $cost " >> rollout.csv
            
            simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 10 > "rollouts/${threads}/${LOSS1}_${LOSS2}.txt"
        done
    done
done
