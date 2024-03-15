#!/bin/bash

memSize=32 #KB
time=1
experimentCount=20

tempDir="blob/temp" #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
greedyExec="./blob/greedy${memSize}_simulator"
stockExec="./blob/stock_simulator"
jsonPath="blob/dep_graph-600K-new.json"
mkdir -p "$tempDir"

echo "[" > "$tempDir/log.json"

echo "Стоковое расписание"
echo "Сборка"
if ! test -f "$stockExec"; then
    python gen.py 0 "$memSize" -1
    rm -rf "$tempDir/work"
    simulation --compiler clang++ "blob/out.json" "$tempDir/work" >> /dev/null
    cd blob/temp/work/generated_code/
    mkdir -p build
    cd build
    cmake ..
    cmake --build . --config Release -- -j4
    cd ../../../../../
    cp ./$tempDir/work/generated_code/bin/simulator "$stockExec"
fi
echo "Прогон"
for i in $(seq 1 $experimentCount); do
    echo "$i/$experimentCount"
    # "./$tempDir/work/generated_code/bin/simulator" "$time" >> "$tempDir/log.json"
    "./$stockExec" "$time" >> "$tempDir/log.json"
    echo "," >> "$tempDir/log.json"
done

echo "Жадное расписание"
echo "Сборка"
if ! test -f "$greedyExec"; then
    python gen.py 4 "$memSize" -1
    rm -rf "$tempDir/work"
    simulation --compiler clang++ -B "blob/out.json" "$tempDir/work" >> /dev/null
    cd blob/temp/work/generated_code/
    mkdir -p build
    cd build
    cmake ..
    cmake --build . --config Release -- -j4
    cd ../../../../../
    cp ./$tempDir/work/generated_code/bin/simulator "$greedyExec"
fi
echo "Прогон"
for i in $(seq 1 $experimentCount); do
    echo "$i/$experimentCount"
    "./$greedyExec" "$time" >> "$tempDir/log.json"
    echo "," >> "$tempDir/log.json"
done

echo "]" >> "$tempDir/log.json"

python plot.py $tempDir 