#!/bin/bash

rm -rf ../bin ../lib ./build
mkdir build
cd build
cmake ..
cmake --build . --config Release -- -j4
cd ..

#cp ../python/cache_study/*.so ../python/gen_schedule/
