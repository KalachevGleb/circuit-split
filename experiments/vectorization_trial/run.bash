#!/bin/bash

g++ -O3 -march=native -DVEC_ON main.cpp -o work
./work $1
