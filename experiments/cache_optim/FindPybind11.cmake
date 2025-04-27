# Note: Данный скрипт полностью написан языковой моделью и недостаточно хорошо протестирован.

# This script finds or fetches Pybind11 if it's not found

if(NOT TARGET pybind11::pybind11)
    include(FetchContent)

    # Set Pybind11 version (default to 2.8.0 if not specified)
    if(NOT DEFINED PYBIND11_VERSION)
        set(PYBIND11_VERSION 2.11)
    endif()

    # Fetch Pybind11
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v${PYBIND11_VERSION}
    )
    FetchContent_GetProperties(pybind11)
    if(NOT pybind11_POPULATED)
        FetchContent_Populate(pybind11)
        add_subdirectory(${pybind11_SOURCE_DIR} ${pybind11_BINARY_DIR})
    endif()
endif()
