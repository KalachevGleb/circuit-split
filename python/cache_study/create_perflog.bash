#!/bin/bash

iters=20

echo "n: stock"
rm -rf blob/stock.perflog

executable="./blob/stock_simulator"
for iter in $(seq $iters); do
    echo "$iter/$iters"

    output=$(perf stat -B -e cache-misses,cache-references,l2_rqsts.all_demand_miss,l2_rqsts.all_demand_references $executable 1 2>&1)
    echo "\"$output\"" >> blob/stock.perflog
done

for n in 1 2 4 8 16 32 64 128 256 512 1024 2048 4096; do
    echo "n: $n"
    rm -rf blob/$n.perflog

    executable="./blob/greedy${n}_simulator"
    for iter in $(seq $iters); do
        echo "$iter/$iters"

        output=$(perf stat -B -e cache-misses,cache-references,l2_rqsts.all_demand_miss,l2_rqsts.all_demand_references $executable 1 2>&1)
        echo "\"$output\"" >> blob/$n.perflog
    done
done