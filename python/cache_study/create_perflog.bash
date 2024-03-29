#!/bin/bash

iters=20

echo "n: stock"
rm -rf "$1/stock.perflog"

executable="$1/stock_simulator"
for iter in $(seq $iters); do
    echo "$iter/$iters"

    output=$(perf stat -B -e cache-misses,cache-references $executable 1 2>&1)
    echo "\"$output\"" >> "$1/stock.perflog"
done

for n in 1 2 4 8 16 32 64 128 256 512 1024 2048 4096; do
    echo "n: $n"
    rm -rf "$1/$n.perflog"

    executable="$1/greedy${n}_simulator"
    for iter in $(seq $iters); do
        echo "$iter/$iters"

        output=$(perf stat -B -e cache-misses,cache-references $executable 1 2>&1)
        echo "\"$output\"" >> "$1/$n.perflog"
    done
done