cmake_minimum_required(VERSION 3.15...4.0)
project(pybind_wrapper)

find_package(pybind11 CONFIG REQUIRED)

python_add_library(pybind_wrapper MODULE src/pyobs_zwoeaf/pybind_wrapper.cpp WITH_SOABI)
target_link_libraries(pybind_wrapper PRIVATE pybind11::headers)
target_link_libraries(pybind_wrapper PRIVATE ${CMAKE_SOURCE_DIR}/lib/lib/x64/libEAFFocuser.a udev)
target_include_directories(pybind_wrapper PUBLIC lib/include/)

install(TARGETS pybind_wrapper DESTINATION pyobs_zwoeaf)
