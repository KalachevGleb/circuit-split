#!/bin/bash

echo 
python gen.py 1 $2 $3 graphs/bitonic13.json cut.json
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 10
echo
python gen.py $1 $2 $3 graphs/bitonic13.json cut.json
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 10
echo
