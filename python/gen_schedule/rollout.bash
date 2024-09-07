#!/bin/bash

if [ "$( cat /proc/sys/kernel/perf_event_paranoid )" != "-1" ]; then
    echo "Настраиваем систему"
    sudo sh -c 'echo -1 > /proc/sys/kernel/perf_event_paranoid'
fi

if command -v python &>/dev/null; then
    echo "Python is available."
else
    echo "Python is not available."
    exit 1
fi

ONLY_BUILD=0
ENABLE_PERF=0
ENABLE_SIMULATION=1
N=20

thread_nums=(1 2 4)
simple_widthes=(1024 2048 4096 8192 16384 32768 65536 131072)
bitonic_widthes=(4 5 6 7 8 9 10 11 12 13 14)
mem_sizes=(256 1024 4096 16384 65536 262144 1048576 4194304 16777216 67108864)

last_dir () {
    name="$1"
    githash="$2"

    # Use find to locate directories matching the pattern
    latest_folder=$(find bin -maxdepth 1 -type d -name "* $name $githash" 2>/dev/null | \
    while read -r dir; do
        # Get the creation time in seconds since epoch
        echo "$(stat -c %W "$dir") $dir"
    done | \
    sort -nr | \
    head -n 1 | \
    awk '{print $2, $3, $4, $5}')

    # Check if a folder was found
    if [ -z "$latest_folder" ]; then
        echo "/dev/null"
    else
        echo "$latest_folder"
    fi
}
last_bin_dir="$( last_dir $1 "$(git rev-parse HEAD)" )"

ts="$( date +"%d.%m.%Y %H:%M:%S" )"
bin_dir="bin/$ts $1 $(git rev-parse HEAD)"
mkdir -p "$bin_dir"

cp "$0" "$bin_dir"
cp gen.py "$bin_dir"

default_compiler="/usr/bin/clang++"

join_by (){
  local d=${1-} f=${2-}
  if shift 2; then
    printf %s "$f" "${@/#/$d}"
  fi
}

progress_bar() {
    local PROG=$1
    local TOTAL=$2
    local WIDTH=50
    local PERC=$(( (PROG * 100) / TOTAL ))
    local FILLED=$(( (PROG * WIDTH) / TOTAL ))
    local EMPTY=$(( WIDTH - FILLED ))

    # Print the progress bar
    printf "\r["
    printf "%${FILLED}s" | tr ' ' '#'
    printf "%${EMPTY}s" | tr ' ' '-'
    printf "] %d%%" "$PERC"
}

execution (){ # json_расписание название компилятор последняя_папка_с_бинарником
    echo "$2"

    bin_name="${2}"

    if [ -f "$3" ]; then
        echo "Используется компилятор ${3}"
        compiler="${3}"
    else
        echo "Используется компилятор по умолчанию ${default_compiler}"
        compiler="${default_compiler}"
    fi

    if [ -z "$4" ] || [ ! -f "$4/$bin_name.json" ] || [ ! -f "$4/$bin_name" ]; then
        echo "Считаю с нуля"
        ../../experiments/bin/simulation "$1" blob/work/ --compiler "${compiler}" -B --run --time 1
        cp "$1" "$bin_dir/${bin_name}.json"
        cp "blob/work/generated_code/bin/simulator" "$bin_dir/$bin_name"
    else
        echo "Использую кэшированные бинарник и расписание"
        cp "$4/$bin_name" "$bin_dir/$bin_name"
        cp "$4/$bin_name.json" "$bin_dir/$bin_name.json"
    fi

    if [ $ONLY_BUILD == 1 ]; then
        echo "Произведена только компиляция"
        return
    fi

    echo "\"$2\"" >> "$bin_dir/$2.txt"
    
    echo "$(python gen.py 100 1 0 "$bin_dir/$bin_name.json" /dev/null --mode 4)" >> "$bin_dir/$2.txt"

    if [ $ENABLE_PERF != 0 ]; then
        for i in $(seq 1 $N); do

            progress_bar $(( i - 1 )) $N

            params=(cache-misses cache-references \
                    L1-dcache-load-misses L1-dcache-loads \
                    l2_rqsts.all_demand_miss l2_rqsts.all_demand_references \
                    l2_rqsts.miss l2_rqsts.references \
                    LLC-load-misses LLC-loads \
                    cycles cycle_activity.cycles_l1d_miss cycle_activity.cycles_l2_miss cycle_activity.cycles_l3_miss \
                    cycle_activity.stalls_l1d_miss cycle_activity.stalls_l2_miss cycle_activity.stalls_l3_miss \
                    cycle_activity.cycles_mem_any cycle_activity.stalls_mem_any \
                    l1d_pend_miss.pending l1d_pend_miss.fb_full l1d_pend_miss.pending_cycles l1d_pend_miss.pending_cycles_any)
            
            echo "{" >> "$bin_dir/$2.txt"

            perf_output=$(perf stat -B -e "$(join_by , "${params[@]}")" "./$bin_dir/$bin_name" 1 2>&1)
            for ((i = 0; i < ${#params[@]}; i++)); do
                param="${params[$i]}"
                value=$(echo "$perf_output" | grep "$param" | tr -d ' \n')
                if [[ $i -lt $((${#params[@]} - 1)) ]]; then
                    echo "\"$param\" : \"$value\"," >> "$bin_dir/$2.txt"
                else
                    echo "\"$param\" : \"$value\"" >> "$bin_dir/$2.txt"
                fi
            done

            echo "}" >> "$bin_dir/$2.txt"
        done
    fi

    progress_bar $N $N
    echo ""

    if [ $ENABLE_SIMULATION != 0 ]; then
        for i in $(seq 1 $N); do
            
            progress_bar $(( $i - 1 )) $N

            echo $("./$bin_dir/$bin_name" 1) >> "$bin_dir/$2.txt"
        done
    fi

    progress_bar $N $N
    echo ""
}

if [ "$1" == "test" ]; then

    python gen.py 1 1 0 "./graphs/50k.json" cut.json --mode 3
    execution  cut.json test_mode_3 "$default_compiler" "$last_bin_dir"

    python gen.py 4 1 0 "./graphs/50k.json" cut.json --mode 5
    execution  cut.json test_mode_5 "$default_compiler" "$last_bin_dir"

elif [ "$1" == "50k" ]; then

    python gen.py 1 1 0 "./graphs/50k.json" cut.json --mode 1
    execution  cut.json 50k_1_dummy "$default_compiler" "$last_bin_dir"

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 50k_${threads}_depth "$default_compiler" "$last_bin_dir"
    done

elif [ "$1" == "600k" ]; then

    python gen.py 1 1 0 "./graphs/600k.json" cut.json --mode 1
    execution  cut.json 600k_1_dummy "$default_compiler" "$last_bin_dir"

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 "./graphs/600k.json" cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 600k_${threads}_depth "$default_compiler" "$last_bin_dir"
    done

elif [ "$1" == "extended_50k" ]; then

    python gen.py 1 1 0 "./graphs/50k.json" cut.json --mode 1
    execution  cut.json real_1_dummy "$default_compiler" "$last_bin_dir" 50

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json real_${threads}_depth "$default_compiler" "$last_bin_dir"
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthdummy "$default_compiler" "$last_bin_dir"
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        execution cut.json real_${threads}_depthshuf "$default_compiler" "$last_bin_dir"
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthshufdummy "$default_compiler" "$last_bin_dir"
    done

elif [ "$1" == "extended_600k" ]; then

    python gen.py 1 1 0 "./graphs/600k.json" cut.json --mode 1
    execution  cut.json real_1_dummy "$default_compiler" "$last_bin_dir" 600

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json real_${threads}_depth "$default_compiler" "$last_bin_dir"
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthdummy "$default_compiler" "$last_bin_dir"
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        execution cut.json real_${threads}_depthshuf "$default_compiler" "$last_bin_dir"
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthshufdummy "$default_compiler" "$last_bin_dir"
    done

elif [ "$1" == 'bitonic' ]; then

    for width in "${bitonic_widthes[@]}"; do
        echo $width
        execution ../gen_graphs/output/bitonic_sort_${width}_one_thread.json 1_stock "$default_compiler" "$last_bin_dir"
        
        for threads in "${thread_nums[@]}"; do
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
            execution cut.json ${threads}_depth "$default_compiler" "$last_bin_dir"
        done
    done

elif [ "$1" == 'simple' ]; then

    depth="$2"
    if [ $depth != 5 ] && [ $depth != 10 ] && [ $depth != 15 ] && [ $depth != 20 ]; then
        echo "Плохое depth"
        exit 1
    fi

    for width in "${simple_widthes[@]}"; do
        for threads in "${thread_nums[@]}"; do
            execution ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json simpled${depth}_${threads}_stock "$default_compiler" "$last_bin_dir" "$width"
            
            python gen.py ${threads} 1 0 ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
            execution cut.json simpled${depth}_${threads}_depth "$default_compiler" "$last_bin_dir" "$width"
        done
    done

elif [ "$1" == 'simpled20' ]; then

    depth=20

    for width in "${simple_widthes[@]}"; do
        for threads in "${thread_nums[@]}"; do
            execution ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json ${threads}_stock "$default_compiler" "$last_bin_dir" "$width"
            
            python gen.py ${threads} 1 0 ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
            execution cut.json ${threads}_depth "$default_compiler" "$last_bin_dir" "$width"
        done
    done

elif [ "$1" == 'simple_extended' ]; then

    depth="$2"
    if [ $depth != 5 ] && [ $depth != 10 ] && [ $depth != 15 ] && [ $depth != 20 ]; then
        echo "Плохое depth"
        exit 1
    fi

    for width in "${simple_widthes[@]}"; do
        for threads in "${thread_nums[@]}"; do
            execution ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json simpled${depth}_${threads}_stock "$default_compiler" "$last_bin_dir" "$width"
            
            python gen.py ${threads} 1 0 ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
            execution cut.json simpled${depth}_${threads}_depth "$default_compiler" "$last_bin_dir" "$width"
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
            execution cut.json simpled${depth}_${threads}_depthshuf "$default_compiler" "$last_bin_dir" "$width"
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
            execution cut.json simpled${depth}_${threads}_depthdummy "$default_compiler" "$last_bin_dir" "$width"
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
            execution cut.json simpled${depth}_${threads}_depthshufdummy "$default_compiler" "$last_bin_dir" "$width"
        done
    done

elif [ "$1" == 'cache_effect' ]; then

    execution ./graphs/bitonic14_th1.json best_bitonic_14 "$default_compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 ./graphs/bitonic14_th1.json cut.json --mode 1
    execution cut.json stock_bitonic_14 "$default_compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 ./graphs/bitonic14_th1.json cut.json --mode 5 --mem_size 64
    execution cut.json cache_bitonic_14 "$default_compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/600k.json stock.json --mode 1
    execution stock.json stock_600k "$default_compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/600k.json cache.json --mode 5 --mem_size 64
    execution cache.json cache_600k "$default_compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/50k.json stock.json --mode 1
    execution stock.json stock_50k "$default_compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/50k.json cache.json --mode 5 --mem_size 64
    execution cache.json cache_50k "$default_compiler" "$last_bin_dir" 0

elif [ "$1" == 'cache_size_50k' ]; then

    python gen.py 1 1 0 graphs/50k.json cut.json --mode 1
    execution cut.json stock "$default_compiler" "$last_bin_dir"

    for mem in "${mem_sizes[@]}"; do
        python gen.py 1 1 0 graphs/50k.json cut.json --mode 5 --mem_size "${mem}"
        execution cut.json "cache_${mem}" "$default_compiler" "$last_bin_dir"
    done


elif [ "$1" == 'cache_size_600k' ]; then

    python gen.py 1 1 0 graphs/600k.json cut.json --mode 1
    execution cut.json stock "$default_compiler" "$last_bin_dir"

    for mem in "${mem_sizes[@]}"; do
        python gen.py 1 1 0 graphs/600k.json cut.json --mode 5 --mem_size "${mem}"
        execution cut.json "cache_${mem}" "$default_compiler" "$last_bin_dir"
    done

elif [ "$1" == 'cache_size_bitonic14' ]; then

    python gen.py 1 1 0 ../graphs/bitonic14_th1.json cut.json --mode 1
    execution cut.json stock "$default_compiler" "$last_bin_dir"

    for mem in "${mem_sizes[@]}"; do
        python gen.py 1 1 0 ../graphs/bitonic14_th1.json cut.json --mode 5 --mem_size "${mem}"
        execution cut.json "cache_${mem}" "$default_compiler" "$last_bin_dir"
    done

elif [ "$1" == 'cache_size_simple' ]; then

    python gen.py 1 1 0 .../graphs/simple_262144_20_th1.json cut.json --mode 1
    execution cut.json stock "$default_compiler" "$last_bin_dir"

    for mem in "${mem_sizes[@]}"; do
        python gen.py 1 1 0 ../graphs/simple_262144_20_th1.json --mode 5 --mem_size "${mem}"
        execution cut.json "cache_${mem}" "$default_compiler" "$last_bin_dir"
    done

else

    echo "Неизвестный режим: $1"
    exit 1

fi
