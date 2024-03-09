#!/bin/bash

tempDir="blob/temp"

mkdir -p "$tempDir"

echo "[" > "$tempDir/log.json"

#simulation --compiler clang++ "../gen_graphs/output/bitonic_sort_11_one_thread.json" "$tempDir/work" -r -t "1" >> "$tempDir/log.json"

python gen.py 0 8 5 > "$tempDir/out.json"
simulation --compiler clang++ "$tempDir/out.json" "$tempDir/work" -r
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"

python gen.py 1 8 5 > "$tempDir/out.json"
simulation --compiler g+clang+ "$tempDir/out.json" "$tempDir/work" -r
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"

python gen.py 2 8 5 > "$tempDir/out.json"
simulation --compiler gclang "$tempDir/out.json" "$tempDir/work" -r
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"
echo "," >> "$tempDir/log.json"
"./$tempDir/work/generated_code/bin/simulator" "3" >> "$tempDir/log.json"

echo "]" >> "$tempDir/log.json"
