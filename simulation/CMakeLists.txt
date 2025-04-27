project(simulation)

add_executable(${PROJECT_NAME} main.cpp)
target_link_libraries(${PROJECT_NAME} utils)

if(UNIX AND NOT APPLE)
    target_link_libraries(${PROJECT_NAME} stdc++fs)
endif()

#add_subdirectory(simfiles)
