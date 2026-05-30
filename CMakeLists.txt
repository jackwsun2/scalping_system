cmake_minimum_required(VERSION 3.20)

project(ScalpingSystem LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(BUILD_DESKTOP_GUI "Build Dear ImGui desktop application" OFF)
option(BUILD_CLI_COMPAT "Build legacy command line compatibility runner" ON)
option(TRADING_FETCH_GUI_DEPS "Download Dear ImGui and GLFW with FetchContent" OFF)
set(TRADING_IMGUI_SOURCE_DIR "" CACHE PATH "Path to Dear ImGui source directory")
set(TRADING_GLFW_SOURCE_DIR "" CACHE PATH "Path to GLFW source directory")

include(FetchContent)
find_package(PkgConfig REQUIRED)
pkg_check_modules(SPDLOG REQUIRED IMPORTED_TARGET spdlog)
pkg_check_modules(SQLITE3 REQUIRED IMPORTED_TARGET sqlite3)

add_library(trading_core
    src/application/trading_service.cpp
    src/domain/backtester.cpp
    src/domain/indicators.cpp
    src/domain/risk.cpp
    src/domain/strategy.cpp
    src/infrastructure/csv_data_source.cpp
    src/infrastructure/file_logger.cpp
    src/infrastructure/sample_data.cpp
    src/infrastructure/sqlite_store.cpp
    src/presentation/app_factory.cpp
)

target_include_directories(trading_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(trading_core
    PUBLIC
        PkgConfig::SPDLOG
        PkgConfig::SQLITE3
)

if(MSVC)
    target_compile_options(trading_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(trading_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(BUILD_CLI_COMPAT)
    add_executable(scalper_cli src/main.cpp src/live_simulator.cpp)
    target_link_libraries(scalper_cli PRIVATE trading_core)
endif()

if(BUILD_DESKTOP_GUI)
    if(TRADING_FETCH_GUI_DEPS)
        FetchContent_Declare(
            glfw
            GIT_REPOSITORY https://github.com/glfw/glfw.git
            GIT_TAG 3.4
        )
        set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
        set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
        set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        FetchContent_MakeAvailable(glfw)

        FetchContent_Declare(
            imgui
            GIT_REPOSITORY https://github.com/ocornut/imgui.git
            GIT_TAG v1.91.9b
        )
        FetchContent_MakeAvailable(imgui)
        set(TRADING_IMGUI_RESOLVED_DIR ${imgui_SOURCE_DIR})
    else()
        if(NOT TRADING_IMGUI_SOURCE_DIR)
            message(FATAL_ERROR "BUILD_DESKTOP_GUI=ON requires -DTRADING_IMGUI_SOURCE_DIR=/path/to/imgui or -DTRADING_FETCH_GUI_DEPS=ON")
        endif()
        if(TRADING_GLFW_SOURCE_DIR)
            set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
            set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
            set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
            add_subdirectory(${TRADING_GLFW_SOURCE_DIR} ${CMAKE_BINARY_DIR}/glfw-local)
        else()
            find_package(glfw3 REQUIRED)
        endif()
        set(TRADING_IMGUI_RESOLVED_DIR ${TRADING_IMGUI_SOURCE_DIR})
    endif()

    add_library(imgui_backend
        ${TRADING_IMGUI_RESOLVED_DIR}/imgui.cpp
        ${TRADING_IMGUI_RESOLVED_DIR}/imgui_demo.cpp
        ${TRADING_IMGUI_RESOLVED_DIR}/imgui_draw.cpp
        ${TRADING_IMGUI_RESOLVED_DIR}/imgui_tables.cpp
        ${TRADING_IMGUI_RESOLVED_DIR}/imgui_widgets.cpp
        ${TRADING_IMGUI_RESOLVED_DIR}/backends/imgui_impl_glfw.cpp
        ${TRADING_IMGUI_RESOLVED_DIR}/backends/imgui_impl_opengl2.cpp
    )
    target_include_directories(imgui_backend
        PUBLIC
            ${TRADING_IMGUI_RESOLVED_DIR}
            ${TRADING_IMGUI_RESOLVED_DIR}/backends
    )
    target_link_libraries(imgui_backend PUBLIC glfw)

    add_executable(scalper_desktop
        src/presentation/gui/desktop_main.cpp
        src/presentation/gui/imgui_desktop_app.cpp
        src/presentation/aux/nana_elements_adapter.cpp
    )
    target_compile_definitions(scalper_desktop PRIVATE TRADING_WITH_IMGUI=1)
    target_link_libraries(scalper_desktop
        PRIVATE
            trading_core
            imgui_backend
    )
    if(APPLE)
        target_link_libraries(scalper_desktop PRIVATE "-framework OpenGL")
    elseif(UNIX)
        find_package(OpenGL REQUIRED)
        target_link_libraries(scalper_desktop PRIVATE OpenGL::GL)
    endif()
endif()

enable_testing()
add_executable(trading_tests tests/trading_tests.cpp)
target_link_libraries(trading_tests PRIVATE trading_core)
add_test(NAME trading_tests COMMAND trading_tests)
