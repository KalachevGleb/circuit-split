#!/bin/bash

mkdir -p rollouts
rm -rf rollouts
mkdir rollouts

for threads in 1 2 4 8; do
    mkdir -p "rollouts/$threads"
    for LOSS1 in 0 1 10 20 30 40 50 60 70 80 90 100: do
        for LOSS2 in 0 1 10 20 30 40 50 60 70 80 90 100; do
            python gen.py $threads $LOSS1 $LOSS2 dep_graph.json cut.txt
            simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 10 >> "rollouts/$threads/${LOSS1}_${LOSS2}.txt"
        done
    done
done