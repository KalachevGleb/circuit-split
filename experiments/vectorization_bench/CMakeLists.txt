cmake_minimum_required(VERSION 3.10)

project(VectorizationBench CXX)

# Общие флаги оптимизации
set(BASELINE_FLAGS -O3)
set(OPTIM_FLAGS -O3 -march=native)

# Создание baseline версии
add_executable(vec_baseline main.cpp)
target_compile_options(vec_baseline PRIVATE ${BASELINE_FLAGS})

# Создание optim версии
add_executable(vec_optim main.cpp)
target_compile_options(vec_optim PRIVATE ${OPTIM_FLAGS})