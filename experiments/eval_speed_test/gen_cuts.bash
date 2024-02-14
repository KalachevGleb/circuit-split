#!/bin/bash

outDir="cuts"
allThreads=(1 2 3 4)
allLOSSes=(100 200 300 500 750 1000 2000 3000 4000 5000 6000 7000 8000 9000 10000 20000 30000 40000 50000 60000 70000 80000 90000 100000)

mkdir -p $outDir

for thread in ${allThreads[@]}; do
    for l in ${allLOSSes[@]}; do
        predictedTime=$(python gen.py $thread $l temp.txt)
        mv temp.txt $outDir/$thread\ $l\ $predictedTime.txt
    done
done
