#!/bin/bash

rm -rf ../bin ../lib ./build
mkdir build
cd build
cmake ..
cmake --build . --config Release -- -j4
cd ..
rm -rf build
rm -rf gen_schedule/cpp*
cp lib/cpp* gen_schedule
