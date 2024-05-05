#!/bin/bash

ts=$( date +"%A, %b %d, %Y %H:%M:%S" )
bin_dir="bin/$ts"

rm -rf blob
mkdir -p "$bin_dir"
cp ./test_hardcode.bash "$bin_dir"

echo 
python gen.py 1 -1 -1 graphs/600k.json cut.json
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_1_-1_-1
echo 
python gen.py 2 1 0 graphs/600k.json cut.json --inside_layer_schedule dummy
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_2_1_0_dummy
echo 
python gen.py 2 1 0 graphs/600k.json cut.json --inside_layer_schedule dummy --shuffle_layers
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_2_1_0_dummy_shuffle
echo 
python gen.py 2 1 0 graphs/600k.json cut.json --inside_layer_schedule backpack
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_2_1_0_backpack
echo 
python gen.py 2 1 0 graphs/600k.json cut.json --inside_layer_schedule backpack --shuffle_layers
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_2_1_0_backpack_shuffle
echo 
python gen.py 4 1 0 graphs/600k.json cut.json --inside_layer_schedule dummy
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_4_1_0_dummy
echo
python gen.py 4 1 0 graphs/600k.json cut.json --inside_layer_schedule dummy --shuffle_layers
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_4_1_0_dummy_shuffle
echo
python gen.py 4 1 0 graphs/600k.json cut.json --inside_layer_schedule backpack
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_4_1_0_backpack
echo
python gen.py 4 1 0 graphs/600k.json cut.json --inside_layer_schedule backpack --shuffle_layers
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 30 >> "$bin_dir/log.txt"
cp blob/work/generated_code/bin/simulator ./$bin_dir/600k_4_1_0_dummy_backpack_shuffle
echo