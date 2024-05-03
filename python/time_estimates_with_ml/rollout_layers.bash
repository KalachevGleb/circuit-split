#!/bin/bash

rm -rf rollout.csv

threads=2
scheme="$1"

for sd in 2 3 7; do
    rm -rf cutted_graphs
    python ../gen_schedule/gen.py ${threads} 1 0 "${scheme}" cut.json --kill_layers True --survive_depth $sd
    
    for cutted_scheme in cutted_graphs/*; do
        output=$(python ../gen_schedule/gen.py ${threads} 1 0 "${cutted_scheme}" cut.json)

        single_thread_cost=$(echo "$output" | grep 'Стоимость однопоточного вычисления:' | grep -oE '\b([0-9]+)')

        A=$(echo "$output" | grep 'Суммарно чтений внутри одного потока:' | grep -oE '\b[0-9]+(\.[0-9]+)?')
        B=$(echo "$output" | grep 'Суммарно чтений между потоками:' | grep -oE '\b[0-9]+(\.[0-9]+)?')
        C=$(echo "$output" | grep 'Суммарно записей:' | grep -oE '\b[0-9]+(\.[0-9]+)?')

        util=$(echo "$output" | grep 'Утилизация потоков:' | grep -oE '\b[0-9]+(\.[0-9]+)?')

        barriers=$(echo "$output" | grep 'Барьеров:' | grep -oE '\b([0-9]+)')

        name="$(basename "$cutted_scheme" .json)"

        out="\"$name\",$threads,$single_thread_cost,$barriers"
        for a in $A; do out="$out,$a"; done
        for b in $B; do out="$out,$b"; done
        for c in $C; do out="$out,$c"; done
        out="$out,$util"
        X=$(echo $out | tr -d '\n' | tr -d ' ')
        
        rm -rf blob
        output=$(simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 3)

        ns_per_node=$(echo "$output" | grep ns_per_node | grep -oE '[0-9]+(\.[0-9]+)')
        ns_per_read=$(echo "$output" | grep ns_per_read | grep -oE '[0-9]+(\.[0-9]+)')

        Y=$(echo "$ns_per_node,$ns_per_read" | tr -d '\n' | tr -d ' ')

        echo "$X,$Y" >> rollout.csv
    done
done