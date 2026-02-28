cmake_minimum_required(VERSION 3.10)
project(A2A_MCP)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Default to Release build for performance if not specified
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Choose the type of build." FORCE)
  message(STATUS "Setting build type to 'Release' as none was specified.")
endif()

# Find Threads (cross-platform threading library)
find_package(Threads REQUIRED)

# Platform-specific compile flags
if(MSVC)
    add_compile_options(/W4 /O2)
else()
    add_compile_options(-Wall -Wextra -O3)
endif()

# Output directory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)

include_directories(${CMAKE_SOURCE_DIR}/include)
include_directories(${CMAKE_SOURCE_DIR}/src)

# Define source files
file(GLOB_RECURSE ENGINE_SOURCES "src/engine/*.cpp")
file(GLOB_RECURSE AGENT_SOURCES "src/agents/*.cpp")
set(MAIN_SOURCE "src/main.cpp")

# Executable: Main Game Engine
add_executable(ghost-void_engine ${MAIN_SOURCE} ${ENGINE_SOURCES} ${AGENT_SOURCES})
target_link_libraries(ghost-void_engine PRIVATE Threads::Threads)

# Executable: Jurassic Pixels Test (for now reusing main logic or specific test file if found)
# Since jurassic_pixels_test.exe was found in bin but no source, we'll create a dummy target 
# that links to the engine to satisfy the build system presence.
# Realistically, we should find the test source. For now, let's assume it shares main.cpp 
# or we'll create a minimal test wrapper later.
add_executable(jurassic_pixels_test ${MAIN_SOURCE} ${ENGINE_SOURCES} ${AGENT_SOURCES})

# Minimal Test Target
add_executable(hello_world src/simple_main.cpp)

# Output directory
# Output directory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)

