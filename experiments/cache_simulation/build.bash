#!/bin/bash

mkdir -p blob

g++ -O3 -Wall -shared -std=c++20 -fPIC $(python3 -m pybind11 --includes) cache.cpp -o blob/cache$(python3-config --extension-suffix)

mv blob/cache$(python3-config --extension-suffix) ../../python/cache_study/

python ../../python/cache_study/gen.py
