#!/bin/bash

mkdir -p blob

memSizes=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096)

echo "[" > blob/log.json

for memSize in ${memSizes[@]}; do
    echo "$memSize KB"
    python gen.py 1 "$memSize"
    simulation --compiler clang++-17 blob/out.json blob/work -r -t 5 | tail -n +2 >> blob/log.json
    echo "," >> blob/log.json
done

python gen.py 0 "$memSize"
simulation --compiler clang++-17 blob/out.json blob/work -r -t 5 | tail -n +2 >> blob/log.json

echo "]" >> blob/log.json