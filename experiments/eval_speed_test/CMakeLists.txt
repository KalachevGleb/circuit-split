project(eval_speed_test)

add_executable(${PROJECT_NAME} main.cpp common.cpp semaphore.cpp line.cpp worker.cpp)
