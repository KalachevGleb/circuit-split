#!/bin/bash

#!/bin/bash

echo 
python gen.py 1 -1 -1 graphs/600k.json cut.json
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 10
cp blob/work/generated_code/bin/simulator ./bin/600k_1_-1_-1
echo 
python gen.py 4 1 0 graphs/600k.json cut.json
simulation cut.json blob/work/ --compiler /usr/bin/g++ --run --time 10
cp blob/work/generated_code/bin/simulator ./bin/600k_4_1_0
echo
