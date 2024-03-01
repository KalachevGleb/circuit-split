#!/bin/bash

python gen.py 0
simulation blob/out.json blob/work -r

python gen.py 1
simulation blob/out.json blob/work -r
