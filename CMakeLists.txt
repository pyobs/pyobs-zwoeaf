cmake_minimum_required(VERSION 3.15...4.0)
project(EAF_focuser)

find_package(pybind11 CONFIG REQUIRED)

find_library(UDEV_LIB NAMES udev libudev REQUIRED)

# The bundled ZWO EAF SDK ships static libraries for several architectures
# under lib/lib/<arch>/. Select the one matching the build target instead of
# always linking the x86-64 build, which fails on ARM hosts (Raspberry Pi and
# similar) with "file in wrong format" at link time.
if(APPLE)
  set(EAF_SDK_ARCH "mac")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64)$")
  set(EAF_SDK_ARCH "armv8")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^armv7")
  set(EAF_SDK_ARCH "armv7")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^armv6")
  set(EAF_SDK_ARCH "armv6")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64)$")
  set(EAF_SDK_ARCH "x64")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(i[3-6]86|x86)$")
  set(EAF_SDK_ARCH "x86")
else()
  message(FATAL_ERROR
    "No bundled ZWO EAF SDK library for CMAKE_SYSTEM_PROCESSOR="
    "'${CMAKE_SYSTEM_PROCESSOR}'. Supported: aarch64/arm64, armv7, armv6, "
    "x86_64, x86, macOS.")
endif()

set(EAF_SDK_LIB "${CMAKE_SOURCE_DIR}/lib/lib/${EAF_SDK_ARCH}/libEAFFocuser.a")
if(NOT EXISTS "${EAF_SDK_LIB}")
  message(FATAL_ERROR "Expected ZWO EAF SDK library not found: ${EAF_SDK_LIB}")
endif()
message(STATUS "Using ZWO EAF SDK library: ${EAF_SDK_LIB}")

python_add_library(EAF_focuser MODULE src/pyobs_zwoeaf/EAF_focuser.cpp WITH_SOABI)
target_link_libraries(EAF_focuser PRIVATE pybind11::headers)
target_link_libraries(EAF_focuser PRIVATE ${EAF_SDK_LIB} ${UDEV_LIB})
target_include_directories(EAF_focuser PUBLIC lib/include/)

install(TARGETS EAF_focuser DESTINATION pyobs_zwoeaf)
