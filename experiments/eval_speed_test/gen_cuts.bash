#!/bin/bash

outDir="cuts"
allThreads=(2 3 4)
allLOSSes=(1.5 1.55 1.6 1.65 1.7 1.75 1.8 1.85 1.9 1.95 2 2.05 2.1 2.15 2.2 2.25)
allLOSSes2=(0.5 0.75 1 1.25 1.5 1.75 2 2.25 2.5 2.75 3 3.25 3.5 3.75)

mkdir -p $outDir

for thread in ${allThreads[@]}; do
    for l1 in ${allLOSSes[@]}; do
        for l2 in ${allLOSSes2[@]}; do
            predictedTime=$(python gen.py $thread $l1 $l2)
            mv cut.txt $outDir/$thread\ $l1\ $l2\ $predictedTime.txt
        done 
    done
done
