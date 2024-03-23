#!/bin/bash

memSize="$1" #KB
time=1
experimentCount=20

tempDir="blob/temp" #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
greedyExec="./blob/greedy${memSize}_simulator"
stockExec="./blob/stock_simulator"
outFile="blob/$1"
mkdir -p "$tempDir"

echo "[" > "$outFile"

echo "Стоковое расписание"
echo "Сборка"
if ! test -f "$stockExec"; then
    python gen.py 0 "$memSize" -1 "blob/stock.json"
    rm -rf "$tempDir"
    simulation --compiler g++ "blob/stock.json" "$tempDir/work" >> /dev/null
    cd blob/temp/work/generated_code/
    mkdir -p build
    cd build
    cmake ..
    cmake --build . --config Release -- -j$2
    cd ../../../../../
    cp ./$tempDir/work/generated_code/bin/simulator "$stockExec"
fi
echo "Прогон"
for i in $(seq 1 $experimentCount); do
    echo "$i/$experimentCount"
    # "./$tempDir/work/generated_code/bin/simulator" "$time" >> "$outFile"
    "./$stockExec" "$time" >> "$outFile"
    echo "," >> "$outFile"
done

echo "Жадное расписание"
echo "Сборка"
if ! test -f "$greedyExec"; then
    python gen.py 4 "$memSize" -1 "blob/${memSize}.json"
    rm -rf "$tempDir"
    simulation --compiler g++ -B "blob/${memSize}.json" "$tempDir/work" >> /dev/null
    cd blob/temp/work/generated_code/
    mkdir -p build
    cd build
    cmake ..
    cmake --build . --config Release -- -j$2
    cd ../../../../../
    cp ./$tempDir/work/generated_code/bin/simulator "$greedyExec"
fi
echo "Прогон"
for i in $(seq 1 $experimentCount); do
    echo "$i/$experimentCount"
    "./$greedyExec" "$time" >> "$outFile"
    echo "," >> "$outFile"
done

echo "]" >> "$outFile"

python plot.py $outFile 
