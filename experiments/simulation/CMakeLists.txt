project(simulation)

add_executable(${PROJECT_NAME} main.cpp)
target_link_libraries(${PROJECT_NAME} utils)

#add_subdirectory(simfiles)
