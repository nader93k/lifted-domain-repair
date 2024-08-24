cmake_minimum_required(VERSION 3.25)
project(datalog_transformer)

set(CMAKE_CXX_STANDARD 20)

add_executable(datalog_transformer
        main.cpp
        parser.cpp
        parser.h
        parser.cpp
        common.h
        transformer.cpp
        transformer.h pretty_print.cpp pretty_print.h common.cpp minizinc_printer.cpp minizinc_printer.h)
