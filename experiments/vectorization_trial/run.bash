#!/bin/bash

g++ -O3 -march=native main.cpp -o work
./work $1
