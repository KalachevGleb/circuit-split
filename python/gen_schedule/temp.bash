#!/bin/bash

mkdir 4

simulation simple_circuit_n8192_d20_th1.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_1_stock
simulation simple_circuit_n8192_d20_th2.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_2_stock
simulation simple_circuit_n8192_d20_th4.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_4_stock

python gen.py 2 1 0 simple_circuit_n8192_d20_th1.json cut.json --mode 3
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_2_depth
python gen.py 3 1 0 simple_circuit_n8192_d20_th1.json cut.json --mode 3
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_3_depth
python gen.py 4 1 0 simple_circuit_n8192_d20_th1.json cut.json --mode 3
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_4_depth

python gen.py 2 1 0 simple_circuit_n8192_d20_th1.json cut.json --mode 1
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_2_greedy_1_0
python gen.py 3 1 0 simple_circuit_n8192_d20_th1.json cut.json --mode 1
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_3_greedy_1_0
python gen.py 4 1 0 simple_circuit_n8192_d20_th1.json cut.json --mode 1
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_4_greedy_1_0

python gen.py 2 1 1 simple_circuit_n8192_d20_th1.json cut.json --mode 1
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_2_greedy_1_1
python gen.py 3 1 1 simple_circuit_n8192_d20_th1.json cut.json --mode 1
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_3_greedy_1_1
python gen.py 4 1 1 simple_circuit_n8192_d20_th1.json cut.json --mode 1
simulation cut.json blob/work/ --compiler /usr/bin/g++ -B --run --time 1
cp blob/work/generated_code/bin/simulator ./4/th_4_greedy_1_1