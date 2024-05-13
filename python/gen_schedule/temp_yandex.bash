#!/bin/bash

N=200

ts=$( date +"%d.%m.%Y %H:%M:%S" )
bin_dir="bin/$ts_$(git rev-parse HEAD)"
mkdir -p "$bin_dir"
echo "" > "$bin_dir/log.txt"

cp "$0" "$bin_dir"

compiler="$1"
if [ -z "$compiler" ]; then
    compiler="/usr/bin/g++"
fi
echo "Используется компилятор $compiler"

execution (){
    echo "$2"

    ../../experiments/bin/simulation "$1" blob/work/ --compiler "$3" -B --run --time 1
    cp "blob/work/generated_code/bin/simulator" "$bin_dir/$2"

    echo "\"$2\"" >> "$bin_dir/log.txt"
    for i in $(seq 1 200); do
        echo "$i/$N"
        echo $("./$bin_dir/$2" 1) >> "$bin_dir/log.txt"
    done
}

execution ../gen_graphs/output/simple_circuit_n8192_d20_th1.json th_1_stock $compiler
# execution ../gen_graphs/output/simple_circuit_n8192_d20_th2.json th_2_stock $compiler
execution ../gen_graphs/output/simple_circuit_n8192_d20_th8.json th_8_stock $compiler

# python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th1.json cut.json --mode 3
# execution cut.json th_2_depth
python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th1.json cut.json --mode 3
execution cut.json th_8_depth

# python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th1.json cut.json --mode 1
# execution cut.json th_2_greedy_1_0
# python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th1.json cut.json --mode 1
# execution cut.json th_4_greedy_1_0

# python gen.py 2 1 1 ../gen_graphs/output/simple_circuit_n8192_d20_th1.json cut.json --mode 1
# execution cut.json th_2_greedy_1_1
# python gen.py 4 1 1 ../gen_graphs/output/simple_circuit_n8192_d20_th1.json cut.json --mode 1
# execution cut.json th_4_greedy_1_1