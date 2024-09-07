#!/bin/bash

rm -rf build
mkdir build
cd build
cmake -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ ..
cmake --build . --config Release -- -j$1
cd ..

cp ../python/cache_study/*.so ../python/gen_schedule/
