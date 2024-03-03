#!/bin/bash

memSizes=(1 2 4 8 16 32 64 128 256 512 1024 2048)

echo "[" > log.txt
for thread in ${memSizes[@]}; do
    echo "$thread KB"
    python gen.py 1 "$thread"
    simulation --compiler clang++ blob/out.json blob/work -r -t 10 >> blob/log.txt
    echo "," >> blob/log.txt
done
echo "]" >> blob/log.txt