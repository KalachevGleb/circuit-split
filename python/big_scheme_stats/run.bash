#!/bin/bash

python txt2pickle.py "$1"
python plot.py

mv hist_ns_per_read.png "$(basename "$1" .txt)_hist.png"
mv bars_ns_per_read.png "$(basename "$1" .txt)_bars.png"