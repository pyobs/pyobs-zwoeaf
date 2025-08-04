cmake_minimum_required(VERSION 3.15...4.0)
project(EAF_focuser)

find_package(pybind11 CONFIG REQUIRED)

python_add_library(EAF_focuser MODULE src/pyobs_zwoeaf/EAF_focuser.cpp WITH_SOABI)
target_link_libraries(EAF_focuser PRIVATE pybind11::headers)
target_link_libraries(EAF_focuser PRIVATE ${CMAKE_SOURCE_DIR}/lib/lib/x64/libEAFFocuser.a udev)
target_include_directories(EAF_focuser PUBLIC lib/include/)

install(TARGETS EAF_focuser DESTINATION pyobs_zwoeaf)
