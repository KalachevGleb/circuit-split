#!/bin/bash

N=200

ts="$( date +"%d.%m.%Y %H:%M:%S" )"
bin_dir="bin/$ts $(git rev-parse HEAD)"
mkdir -p "$bin_dir"
echo "" > "$bin_dir/log.txt"

last_bin_dir="$(ls -td bin/*/ | head -1)"

cp "$0" "$bin_dir"

compiler="/usr/bin/g++"
echo "Используется компилятор $compiler"

execution (){
    echo "$2"

    if [ -z "$4" ] || [ ! -f "$4/$2" ]; then
        ../../experiments/bin/simulation "$1" blob/work/ --compiler "$3" -B --run --time 1
        cp "blob/work/generated_code/bin/simulator" "$bin_dir/$2"
    else
        cp "$4/$2" "$bin_dir/$2"
    fi

    echo "\"$2\"" >> "$bin_dir/$5.txt"
    for i in $(seq 1 200); do
        echo "$i/$N"
        echo $("./$bin_dir/$2" 1) >> "$bin_dir/log.txt"
    done
}

for width in "8192" "16384" "32768" "65536" "131072"; do
    execution ../gen_graphs/output/simple_circuit_n${width}_d20_th1.json 1_stock $compiler $last_bin_dir
    python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
    execution cut.json 1_depth $compiler $last_bin_dir
    # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
    # execution cut.json 1_depth_shuf $compiler $last_bin_dir
    # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
    # execution cut.json 1_depth_dummy $compiler $last_bin_dir
    # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
    # execution cut.json 1_depth_shuf_dummy $compiler $last_bin_dir

    execution ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json 2_stock $compiler $last_bin_dir
    python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
    execution cut.json 2_depth $compiler $last_bin_dir
    # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
    # execution cut.json 2_depth_shuf $compiler $last_bin_dir
    # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
    # execution cut.json 2_depth_dummy $compiler $last_bin_dir
    # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
    # execution cut.json 2_depth_shuf_dummy $compiler $last_bin_dir

    execution ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json 4_stock $compiler $last_bin_dir
    python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
    execution cut.json 4_depth $compiler $last_bin_dir
    # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
    # execution cut.json 4_depth_shuf $compiler $last_bin_dir
    # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
    # execution cut.json 4_depth_dummy $compiler $last_bin_dir
    # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
    # execution cut.json 4_depth_shuf_dummy $compiler $last_bin_dir

    execution ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json 8_stock $compiler $last_bin_dir
    python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
    execution cut.json 8_depth $compiler $last_bin_dir
    # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
    # execution cut.json 8_depth_shuf $compiler $last_bin_dir
    # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
    # execution cut.json 8_depth_dummy $compiler $last_bin_dir
    # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
    # execution cut.json 8_depth_shuf_dummy $compiler $last_bin_dir
done