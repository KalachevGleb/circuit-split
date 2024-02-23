project(utils)

get_filename_component(UTILS_SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR} ABSOLUTE)
add_definitions(-DUTILS_SRC_DIR="${UTILS_SRC_DIR}")

add_library(${PROJECT_NAME} STATIC json.cpp argparse.cpp utils.cpp)

target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
