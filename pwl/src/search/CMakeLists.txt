cmake_minimum_required(VERSION 3.9)
project(search)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_OSX_ARCHITECTURES arm64)

# Detect the architecture
if(APPLE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -arch arm64")
endif()

if (CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_CONFIGURATION_TYPES Debug Release)
endif ()

# Find Boost and set it up
set(Boost_USE_STATIC_LIBS OFF)
set(Boost_USE_MULTITHREADED ON)
set(Boost_USE_STATIC_RUNTIME OFF)
find_package(Boost REQUIRED COMPONENTS program_options)

if (Boost_FOUND)
    include_directories(${Boost_INCLUDE_DIRS})
    link_directories(${Boost_LIBRARY_DIRS})
    add_definitions("-DHAS_BOOST")
else()
    message(FATAL_ERROR "Boost not found. Please install Boost and try again.")
endif()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wnon-virtual-dtor")

# Release flags
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -g -DNDEBUG -fomit-frame-pointer")

# Debug flags
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -fsanitize=undefined -fno-omit-frame-pointer")

# Define source files
file(GLOB_RECURSE SOURCE_FILES 
    "*.cc"
    "*.h"
    "*.tpp"
)

# Add executable
add_executable(search ${SOURCE_FILES})

# Include directories
target_include_directories(search PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Link Boost libraries
target_link_libraries(search PRIVATE ${Boost_LIBRARIES})

# Output the build type and architecture
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Target architecture: ${CMAKE_OSX_ARCHITECTURES}")