#!/bin/bash

if [ $(cat /proc/sys/kernel/perf_event_paranoid) != "-1" ]; then
    echo "Настраиваем систему"
    sudo sh -c 'echo -1 > /proc/sys/kernel/perf_event_paranoid'
fi

N=200

ts="$( date +"%d.%m.%Y %H:%M:%S" )"
bin_dir="bin/$ts $(git rev-parse HEAD)"
mkdir -p "$bin_dir"
# echo "" > "$bin_dir/log.txt"

last_bin_dir="$(ls -td bin/*/ | head -1)"

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
        ../../experiments/bin/simulation "$1" blob/work/ --compiler "$3" -B --run --time 1
        cp "$1" "$bin_dir/${bin_name}.json"
        cp "blob/work/generated_code/bin/simulator" "$bin_dir/$bin_name"
    else
        cp "$4/$bin_name" "$bin_dir/$bin_name"
        cp "$4/$bin_name.json" "$bin_dir/$bin_name.json"
    fi

    echo "\"$2\"" >> "$bin_dir/$5.txt"
    
    echo "$(python gen.py 100 1 0 "$1" /dev/null --mode 4)" >> "$bin_dir/$5.txt"

    for i in $(seq 1 $N); do
        echo "perf $i/$N"

        output=$(perf stat -B -e cache-misses,cache-references,l2_rqsts.all_demand_miss,l2_rqsts.all_demand_references "./$bin_dir/$bin_name" 1 2>&1)

        echo "{" >> "$bin_dir/$5.txt"
        echo "\"cache-misses\" : \"$(echo "$output" | grep "cache-misses" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"cache-references\" : \"$(echo "$output" | grep "cache-references" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"l2_rqsts.all_demand_miss\" : \"$(echo "$output" | grep "l2_rqsts.all_demand_miss" | tr -d ' \n')\"," >> "$bin_dir/$5.txt"
        echo "\"l2_rqsts.all_demand_references\" : \"$(echo "$output" | grep "l2_rqsts.all_demand_references" | tr -d ' \n')\"" >> "$bin_dir/$5.txt"
        echo "}" >> "$bin_dir/$5.txt"
    done

    for i in $(seq 1 $N); do
        echo "simulation $i/$N"
        echo $("./$bin_dir/$bin_name" 1) >> "$bin_dir/$5.txt"
    done
}

if [ "$1" == 'pc' ]; then
    for width in "8192"; do
        execution ../gen_graphs/output/simple_circuit_n${width}_d20_th1.json 1_stock "$compiler" "$last_bin_dir" "$width"
        python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 1_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 1_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 1_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 1_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"

        execution ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json 2_stock "$compiler" "$last_bin_dir" "$width"
        python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 2_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 2_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 2_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 2_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"

        execution ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json 4_stock "$compiler" "$last_bin_dir" "$width"
        python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 4_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 4_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 4_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 4_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"

        # execution ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json 8_stock "$compiler" "$last_bin_dir" "$width"
        # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        # execution cut.json 8_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 8_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 8_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 8_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"
    done
elif [ "$1" == 'server' ]; then
    for width in "8192" "16384" "32768" "65536" "131072"; do
        execution ../gen_graphs/output/simple_circuit_n${width}_d20_th1.json 1_stock "$compiler" "$last_bin_dir" "$width"
        python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 1_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 1_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 1_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 1 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 1_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"

        execution ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json 2_stock "$compiler" "$last_bin_dir" "$width"
        python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 2_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 2_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 2_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 2 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th2.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 2_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"

        execution ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json 4_stock "$compiler" "$last_bin_dir" "$width"
        python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 4_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 4_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 4_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 4 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th4.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 4_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"

        execution ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json 8_stock "$compiler" "$last_bin_dir" "$width"
        python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule backpack
        execution cut.json 8_depth "$compiler" "$last_bin_dir" "$width"
        # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule backpack
        # execution cut.json 8_depth_shuf "$compiler" "$last_bin_dir" "$width"
        # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers False --inside_layer_schedule dummy
        # execution cut.json 8_depth_dummy "$compiler" "$last_bin_dir" "$width"
        # python gen.py 8 1 0 ../gen_graphs/output/simple_circuit_n${width}_d20_th8.json cut.json --mode 3 --shuffle_layers True --inside_layer_schedule dummy
        # execution cut.json 8_depth_shuf_dummy "$compiler" "$last_bin_dir" "$width"
    done
else
    echo "Неизвестное устройство: $1"
    exit 1
fi