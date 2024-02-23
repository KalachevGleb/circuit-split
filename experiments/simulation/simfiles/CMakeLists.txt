project(simulator)
cmake_minimum_required(VERSION 3.16)

set(CMAKE_CXX_STANDARD 20)

file(GLOB ${PROJECT_NAME}_SRC gen_circuit*.cpp)

add_executable(simulator sim.cpp ${${PROJECT_NAME}_SRC})
#target_include_directories(simulator PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../../utils)
# output executable to bin directory in source directory
set_target_properties(${PROJECT_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)
