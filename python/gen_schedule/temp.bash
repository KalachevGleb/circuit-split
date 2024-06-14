#!/bin/bash

if [ "$( cat /proc/sys/kernel/perf_event_paranoid )" != "-1" ]; then
    echo "Настраиваем систему"
    sudo sh -c 'echo -1 > /proc/sys/kernel/perf_event_paranoid'
fi

N=200
thread_nums=(1 2 4)
simple_widthes=(128 256 512 1024 2048 4096 8192 16384 32768 65536 131072)
bitonic_widthes=(4 5 6 7 8 9 10 11 12 13 14)

last_bin_dir="$(ls -td bin/*/ | head -1)"

ts="$( date +"%d.%m.%Y %H:%M:%S" )"
bin_dir="bin/$ts $(git rev-parse HEAD)"
mkdir -p "$bin_dir"
# echo "" > "$bin_dir/log.txt"

cp "$0" "$bin_dir"

compiler="/usr/bin/clang++"
echo "Используется компилятор $compiler"

# genpy2json (){
#     local data="$1"
#     # Извлечение нужных строк
#     extracted=$(echo "$data" | grep -E "^(syncs|max syncs|reads|writes)")

#     # Создание JSON-словаря
#     json=$(echo "$extracted" | awk -F: '
#     {
#         key = $1;
#         value = $2;
#         gsub(/^[ \t]+|[ \t]+$/, "", key);   # Удаление пробелов в начале и конце ключа
#         gsub(/^[ \t]+|[ \t]+$/, "", value); # Удаление пробелов в начале и конце значения
#         gsub(/"/, "\\\"", key);             # Экранирование кавычек в ключе
#         gsub(/"/, "\\\"", value);           # Экранирование кавычек в значении
#         if (value ~ /^\[/) {
#             print "\"" key "\": " value ","
#         } else if (value ~ /^[0-9]+(\.[0-9]+)?$/) {
#             print "\"" key "\": " value ","
#         } else {
#             print "\"" key "\": \"" value "\","
#         }
#     }' | sed '$s/,$//')

#     # Обертывание в JSON-объект
#     json="{${json}}"

#     # Преобразование и вывод в отформатированный JSON с помощью jq
#     echo "$json" | jq .
# }

# perf2json (){
#     local data="$1"

#     json_with_error=$(echo "$data" | grep -E "cache-misses|cache-references|l2_rqsts.all_demand_miss|l2_rqsts.all_demand_references" | awk '
#     BEGIN {
#         print "{"
#     }
#     {
#         # Удаление неразрывных пробелов и замена их на обычные пробелы
#         gsub(/\u202F/, " ");
        
#         # Удаление лишних пробелов и разделение строки на значения и ключи
#         gsub(/[[:space:]]+/, " "); # Замена любых пробелов на один пробел
#         split($0, arr, " "); # Разделение строки по пробелам
#         value = arr[1];
#         key = arr[2];

#         # Удаление лишних пробелов из ключей
#         gsub(/^[ \t]+|[ \t]+$/, "", key);
        
#         # Удаление всех пробелов из значений
#         gsub(/[ \t]+/, "", value);
        
#         # Формирование JSON-строки
#         printf "\"%s\": \"%s\",\n", key, value
#     }
#     END {
#         print "}"
#     }')

#     json="$(echo "$json_with_error" | tr -d " \n" | rev | cut -c3- | rev)}"
#     echo $json
# }

execution (){
    echo "$2"

    bin_name="$5_$2"

    if [ -z "$4" ] || [ ! -f "$4/$bin_name.json" ] || [ ! -f "$4/$bin_name" ]; then
        echo "Считаю с нуля"
        ../../experiments/bin/simulation "$1" blob/work/ --compiler "$3" -B --run --time 1
        cp "$1" "$bin_dir/${bin_name}.json"
        cp "blob/work/generated_code/bin/simulator" "$bin_dir/$bin_name"
    else
        echo "Использую кэшированные бинарник и расписание"
        cp "$4/$bin_name" "$bin_dir/$bin_name"
        cp "$4/$bin_name.json" "$bin_dir/$bin_name.json"
    fi

    echo "\"$2\"" >> "$bin_dir/$5.txt"
    
    echo "$(python gen.py 100 1 0 "$1" /dev/null --mode 4)" >> "$bin_dir/$5.txt"

    #perf-часть

    for i in $(seq 1 $N); do
        echo "perf $i/$N"

        output=$(perf stat -B -e cache-misses,cache-references,l2_rqsts.all_demand_miss,l2_rqsts.all_demand_references,cycles,cycle_activity.cycles_l1d_miss,cycle_activity.cycles_l2_miss,cycle_activity.cycles_l3_miss "./$bin_dir/$bin_name" 1 2>&1)

        echo "{" >> "$bin_dir/$5.txt"
        echo "\"cache-misses\" : \"$(echo "$output" | grep "cache-misses" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"cache-references\" : \"$(echo "$output" | grep "cache-references" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"l2_rqsts.all_demand_miss\" : \"$(echo "$output" | grep "l2_rqsts.all_demand_miss" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"l2_rqsts.all_demand_references\" : \"$(echo "$output" | grep "l2_rqsts.all_demand_references" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"cycles\" : \"$(echo "$output" | grep "cycles       " | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"cycle_activity.cycles_l1d_miss\" : \"$(echo "$output" | grep "cycle_activity.cycles_l1d_miss" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"cycle_activity.cycles_l2_miss\" : \"$(echo "$output" | grep "cycle_activity.cycles_l2_miss" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"cycle_activity.cycles_l3_miss\" : \"$(echo "$output" | grep "cycle_activity.cycles_l3_miss" | tr -d ' \n')\"" >> "$bin_dir/$5.txt"
        echo "}" >> "$bin_dir/$5.txt"
    done

    for i in $(seq 1 $N); do
        echo "simulation $i/$N"
        echo $("./$bin_dir/$bin_name" 1) >> "$bin_dir/$5.txt"
    done
}

if [ "$1" == "real" ]; then

    python gen.py 1 1 0 "./graphs/50k.json" cut.json --mode 1
    execution  cut.json real_1_dummy "$compiler" "$last_bin_dir" 50

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json real_${threads}_depth "$compiler" "$last_bin_dir" 50
    done

    python gen.py 1 1 0 "./graphs/600k.json" cut.json --mode 1
    execution  cut.json real_1_dummy "$compiler" "$last_bin_dir" 600

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 "./graphs/600k.json" cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json real_${threads}_depth "$compiler" "$last_bin_dir" 600
    done

elif [ "$1" == "real_extended" ]; then

    python gen.py 1 1 0 "./graphs/50k.json" cut.json --mode 1
    execution  cut.json real_1_dummy "$compiler" "$last_bin_dir" 50

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json real_${threads}_depth "$compiler" "$last_bin_dir" 50
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthdummy "$compiler" "$last_bin_dir" 50
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        execution cut.json real_${threads}_depthshuf "$compiler" "$last_bin_dir" 50
        python gen.py ${threads} 1 0 ."/graphs/50k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthshufdummy "$compiler" "$last_bin_dir" 50
    done

    python gen.py 1 1 0 "./graphs/600k.json" cut.json --mode 1
    execution  cut.json real_1_dummy "$compiler" "$last_bin_dir" 600

    for threads in "${thread_nums[@]}"; do
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json real_${threads}_depth "$compiler" "$last_bin_dir" 600
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthdummy "$compiler" "$last_bin_dir" 600
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        execution cut.json real_${threads}_depthshuf "$compiler" "$last_bin_dir" 600
        python gen.py ${threads} 1 0 ."/graphs/600k.json cut.json" --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        execution cut.json real_${threads}_depthshufdummy "$compiler" "$last_bin_dir" 600
    done

elif [ "$1" == 'bitonic' ]; then

    for width in "${bitonic_widthes[@]}"; do
        echo $width
        execution ../gen_graphs/output/bitonic_sort_${width}_one_thread.json bitonic_1_stock "$compiler" "$last_bin_dir" "$width"
        
        for threads in "${thread_nums[@]}"; do
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
            execution cut.json bitonic_${threads}_depth "$compiler" "$last_bin_dir" "$width"
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
            execution ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json simpled${depth}_${threads}_stock "$compiler" "$last_bin_dir" "$width"
            
            python gen.py ${threads} 1 0 ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
            execution cut.json simpled${depth}_${threads}_depth "$compiler" "$last_bin_dir" "$width"
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
            execution ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json simpled${depth}_${threads}_stock "$compiler" "$last_bin_dir" "$width"
            
            python gen.py ${threads} 1 0 ../gen_graphs/output/simple_circuit_n${width}_d${depth}_th${threads}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
            execution cut.json simpled${depth}_${threads}_depth "$compiler" "$last_bin_dir" "$width"
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
            execution cut.json simpled${depth}_${threads}_depthshuf "$compiler" "$last_bin_dir" "$width"
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
            execution cut.json simpled${depth}_${threads}_depthdummy "$compiler" "$last_bin_dir" "$width"
            python gen.py ${threads} 1 0 ../gen_graphs/output/bitonic_sort_${width}.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
            execution cut.json simpled${depth}_${threads}_depthshufdummy "$compiler" "$last_bin_dir" "$width"
        done
    done

elif [ "$1" == 'cache' ]; then

    execution ../gen_graphs/output/bitonic_sort_14_one_thread.json best_bitonic_14 "$compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 ../gen_graphs/output/bitonic_sort_14.json cut.json --mode 1
    execution cut.json stock_bitonic_14 "$compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 ../gen_graphs/output/bitonic_sort_14.json cut.json --mode 5 --mem_size 64
    execution cut.json cache_bitonic_14 "$compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/600k.json stock.json --mode 1
    execution stock.json stock_600k "$compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/600k.json cache.json --mode 5 --mem_size 64
    execution cache.json cache_600k "$compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/50k.json stock.json --mode 1
    execution stock.json stock_50k "$compiler" "$last_bin_dir" 0

    python gen.py 1 1 0 graphs/50k.json cache.json --mode 5 --mem_size 64
    execution cache.json cache_50k "$compiler" "$last_bin_dir" 0

elif [ "$1" == 'cache_bitonic' ]; then

    python gen.py 1 1 0 ../gen_graphs/output/bitonic_sort_14.json cut.json --mode 1
    execution cut.json stock_bitonic_14 "$compiler" "$last_bin_dir" 1

    for mem in 8 16 32 64 128 256 512 1024 2048 4096 8192; do
        python gen.py 1 1 0 ../gen_graphs/output/bitonic_sort_14.json cut.json --mode 5 --mem_size "${mem}"
        execution cut.json "cache_bitonic_14_${mem}" "$compiler" "$last_bin_dir" 1

else

    echo "Неизвестный режим: $1"
    exit 1

fi