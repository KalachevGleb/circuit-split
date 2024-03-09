#!/bin/bash

tempDir="blob/temp3" #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
randomness="$1"

mkdir -p "$tempDir"

memSizes=(1 2 4 8 1 2 4 8 1 2 4 8 1 2 4 8)

echo "[" > "$tempDir/log.json"

for memSize in ${memSizes[@]}; do
    echo "$memSize KB"

    simulation --compiler clang++ "../gen_graphs/output/bitonic_sort_11_one_thread.json" "$tempDir/work" -r -t "20" >> "$tempDir/log.json"

    echo "," >> "$tempDir/log.json"
done

for memSize in ${memSizes[@]}; do
    echo "$memSize KB"

    python gen.py 1 "$memSize" "$randomness" > "$tempDir/out.json"
    simulation --compiler g++ "$tempDir/out.json" "$tempDir/work" -r -t "20" >> "$tempDir/log.json"

    echo "," >> "$tempDir/log.json"
done

for memSize in ${memSizes[@]}; do
    echo "$memSize KB"

    python gen.py 0 "$memSize" "$1" > "$tempDir/out.json"
    simulation --compiler clang++ "$tempDir/out.json" "$tempDir/work" -r -t "20" >> "$tempDir/log.json"

    echo "," >> "$tempDir/log.json"
done

echo "]" >> "$tempDir/log.json"
