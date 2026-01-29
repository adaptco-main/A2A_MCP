cmake_minimum_required(VERSION 3.10)

project(ghostvoid)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# Find all source files in src subdirectories
file(GLOB_RECURSE SOURCES 
    "src/engine/*.cpp"
    "src/qube/*.cpp"
    "src/bridge/*.cpp"
    "src/safety/*.cpp"
)

# Exclude main.cpp from the shared library
list(FILTER SOURCES EXCLUDE REGEX "src/main.cpp$")

# Create the shared library
add_library(ghostvoid SHARED ${SOURCES})

# Ensure the output name is libghostvoid.so (or .dll on Windows)
set_target_properties(ghostvoid PROPERTIES PREFIX "lib")

if (WIN32)
    # create a proper libghostvoid.dll on windows
    set_target_properties(ghostvoid PROPERTIES SUFFIX ".dll")
endif()
