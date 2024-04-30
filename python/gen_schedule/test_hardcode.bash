#!/bin/bash

TRIALS=200
ROLLOUT_TIME=1
GRAPH_PATH="graphs/600k.json"

ts=$( date +"%d.%m.%Y %H:%M:%S" )
bin_dir="bin/$ts"

rm -rf blob
mkdir -p "$bin_dir"
cp ./test_hardcode.bash "$bin_dir"

gen_and_simulate() {
    python gen.py "$1" 1 0 "$GRAPH_PATH" cut.json --mode 3 --inside_layer_schedule "$2" --shuffle_layers "$3"
    echo "\"python gen.py $1 1 0 $GRAPH_PATH cut.json --mode 3 --inside_layer_schedule $2 --shuffle_layers $3\"" >> "$bin_dir/log.txt"

    rm -rf blob/work
    simulation cut.json blob/work/ --compiler /usr/bin/g++
    cd blob/work/generated_code
    mkdir -p build
    cd build
    cmake ..
    cmake --build . --config Release
    cd ../../../../
    cp blob/work/generated_code/bin/simulator "./$bin_dir/600k_$1_1_0_$2_$3"

    for i in $(seq 1 "$TRIALS"); do
    echo "$i/$TRIALS"
        "./$bin_dir/600k_$1_1_0_$2_$3" $ROLLOUT_TIME >> "$bin_dir/log.txt"
    done
}

gen_and_simulate 1 dummy "False"
echo
gen_and_simulate 1 dummy "True"
echo

for inside_layer_schedule in "dummy" "backpack"; do
    for shuffle_layers in "False" "True"; do
        for threads in 2 4; do
            gen_and_simulate "$threads" "$inside_layer_schedule" "$shuffle_layers"
            echo
        done
    done
done