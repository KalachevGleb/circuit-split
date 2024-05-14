#!/bin/bash

N=200

ts="$( date +"%d.%m.%Y %H:%M:%S" )"
bin_dir="bin/$ts $(git rev-parse HEAD)"
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

execution ../gen_graphs/output/simple_circuit_n8192_d20_th1.json 1_stock $compiler
python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
execution cut.json 1_depth $compiler
# python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
# execution cut.json 1_depth_shuf $compiler
# python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
# execution cut.json 1_depth_dummy $compiler
# python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
# execution cut.json 1_depth_shuf_dummy $compiler

execution ../gen_graphs/output/simple_circuit_n8192_d20_th2.json 2_stock $compiler
python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
execution cut.json 2_depth $compiler
# python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
# execution cut.json 2_depth_shuf $compiler
# python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
# execution cut.json 2_depth_dummy $compiler
# python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
# execution cut.json 2_depth_shuf_dummy $compiler

execution ../gen_graphs/output/simple_circuit_n8192_d20_th4.json 4_stock $compiler
python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
execution cut.json 4_depth $compiler
# python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
# execution cut.json 4_depth_shuf $compiler
# python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
# execution cut.json 4_depth_dummy $compiler
# python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
# execution cut.json 4_depth_shuf_dummy $compiler

execution ../gen_graphs/output/simple_circuit_n8192_d20_th8.json 8_stock $compiler
python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
execution cut.json 8_depth $compiler
# python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
# execution cut.json 8_depth_shuf $compiler
# python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
# execution cut.json 8_depth_dummy $compiler
# python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n8192_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
# execution cut.json 8_depth_shuf_dummy $compiler