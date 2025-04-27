cmake_minimum_required(VERSION 3.12)
project(cache_study)

# Стандарт C++
set(CMAKE_CXX_STANDARD 20)

# =============================
# Создание venv на этапе конфигурации
# =============================
set(VENV_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../venv")

# Найти системный Python3
find_program(PYTHON3_EXECUTABLE python3)

if(NOT PYTHON3_EXECUTABLE)
    message(FATAL_ERROR "Python3 not found!")
endif()

# Проверяем, есть ли уже venv
if(NOT EXISTS "${VENV_DIR}/bin/activate")
    message(STATUS "Creating Python venv in ${VENV_DIR}")
    execute_process(
        COMMAND "${PYTHON3_EXECUTABLE}" -m venv "${VENV_DIR}"
        RESULT_VARIABLE VENV_RESULT
    )
    if(NOT VENV_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to create Python venv")
    endif()
endif()

# Установим пути для инклудов и либ из venv
set(PYTHON_INCLUDE_DIR "${VENV_DIR}/include")
set(PYTHON_LIBRARY_DIR "${VENV_DIR}/lib")

# =============================
# Pybind11
# =============================
set(PYBIND11_VERSION 2.11)

# Подключение Pybind11
include(FindPybind11.cmake)

# Add source files
set(SOURCES
    cache.cpp
    layer.cpp
    py.cpp
)

# Создание модуля
pybind11_add_module(cpp ${SOURCES})

# Оптимизации
target_compile_options(cpp PRIVATE -O3 -Wall)

# Установим инклуды и либы из venv
target_include_directories(cpp PRIVATE "${PYTHON_INCLUDE_DIR}")
link_directories("${PYTHON_LIBRARY_DIR}")
