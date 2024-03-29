cmake_policy(SET CMP0048 NEW)  # ??? to disable warning in CMake >=3.20
project(experiments)
cmake_minimum_required(VERSION 3.16)

# output to the bin directory (in the current directory)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin")

set(CMAKE_CXX_STANDARD 20)
add_subdirectory(utils)
add_subdirectory(eval_speed_test)
add_subdirectory(layer_by_layer_test)
add_subdirectory(thread_sync_test)
add_subdirectory(simulation)
add_subdirectory(cache_simulation)
add_subdirectory(cache_profiling)
