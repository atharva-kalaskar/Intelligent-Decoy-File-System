cmake_minimum_required(VERSION 3.10)
project(IntelligentDecoyMonitor C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

include_directories(src)

set(SOURCES
    src/main.c
    src/watcher.c
    src/event_logger.c
)

add_executable(monitor ${SOURCES})

# Link standard Windows libraries
target_link_libraries(monitor kernel32 user32)

set_target_properties(monitor PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)
