cmake_minimum_required(VERSION 3.10)
project(LimitOrderBookEngine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PYBIND11_FINDPYTHON ON)

find_package(pybind11 REQUIRED)

pybind11_add_module(limit_order_book 
    bindings/wrapper.cpp
)

target_compile_options(limit_order_book PRIVATE "-O3" "-march=native")