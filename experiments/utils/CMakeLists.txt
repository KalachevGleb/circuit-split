project(utils)

add_library(${PROJECT_NAME} STATIC json.cpp)

target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
