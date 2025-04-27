cmake_minimum_required(VERSION 3.16)

project(experiments)

# Устанавливаем директории вывода
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../bin")   # .exe файлы
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../lib")   # .so файлы
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../lib")   # .a файлы (статические библиотеки)

# Стандарт C++
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Подпроекты
add_subdirectory(utils)
add_subdirectory(simulation)
add_subdirectory(cache_optim)
add_subdirectory(vectorization_bench)