#!/bin/bash

memSizes=(1 2 4 8 16 32 64 128 256 512 1024)

echo "MODE == 0"
if ! test -f ./simulator; then
    python gen.py 0
    simulation blob/out.json blob/work -r
    cp blob/work/generated_code/bin/simulator ./simulator
fi
./simulator 1

echo ""
echo "MODE == 1"
python gen.py 1
simulation blob/out.json blob/work -r