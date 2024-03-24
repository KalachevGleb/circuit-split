cmake_minimum_required(VERSION 3.12)
project(cache_study)

# Set Pybind11 version (optional)
set(PYBIND11_VERSION 2.11)

# Include the script to find or fetch Pybind11
include(FindPybind11.cmake)

set(CMAKE_CXX_STANDARD 20)

# Add source files
set(SOURCES
    cache.cpp
    layer.cpp
    py.cpp
)

# Create a shared library from the source files
pybind11_add_module(cpp ${SOURCES})

# Set optimization and warning flags
target_compile_options(cpp PRIVATE -O3 -Wall)

# Move the compiled library to the desired location
set_target_properties(cpp PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../../python/cache_study/")
