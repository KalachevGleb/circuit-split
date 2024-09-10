#!/bin/bash

echo "Стандартная архитектура, выбранная g++"
echo ""
g++ main.cpp -O3 -o work
./work 0

echo "march=native в g++"
echo ""
g++ main.cpp -O3 -march=native -DVEC_ON -o work
./work 0

rm -rf work
