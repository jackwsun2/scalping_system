#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${BUILD_DIR:-${ROOT_DIR}/build}"
BUILD_TYPE="${BUILD_TYPE:-Release}"
RUN_TESTS=1
CLEAN=0
BUILD_DESKTOP_GUI=0
BUILD_CLI_COMPAT=1
FETCH_GUI_DEPS=0
IMGUI_SOURCE_DIR=""
GLFW_SOURCE_DIR=""
CMAKE_GENERATOR="${CMAKE_GENERATOR:-}"
JOBS="${JOBS:-}"
EXTRA_CMAKE_ARGS=()
EXTRA_BUILD_ARGS=()

usage() {
    cat <<'USAGE'
Usage: ./build.sh [options] [-- <extra cmake configure args>]

Options:
  -h, --help                  Show this help message.
  -b, --build-dir DIR         Build directory. Default: ./build
  -t, --type TYPE             CMake build type. Default: Release
  -j, --jobs N                Parallel build jobs.
      --debug                 Shortcut for --type Debug.
      --release               Shortcut for --type Release.
      --clean                 Remove the build directory before configuring.
      --no-tests              Build only, skip ctest.
      --gui                   Build the Dear ImGui desktop application.
      --no-cli                Disable the legacy CLI compatibility runner.
      --fetch-gui-deps        Let CMake download ImGui and GLFW for GUI builds.
      --imgui-dir DIR         Dear ImGui source directory for GUI builds.
      --glfw-dir DIR          GLFW source directory for GUI builds.
      --generator NAME        CMake generator name.

Environment:
  BUILD_DIR, BUILD_TYPE, JOBS, CMAKE_GENERATOR can also set defaults.

Examples:
  ./build.sh
  ./build.sh --debug --clean
  ./build.sh --gui --fetch-gui-deps
  ./build.sh --gui --imgui-dir ../imgui
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -b|--build-dir)
            BUILD_DIR="$2"
            shift 2
            ;;
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -j|--jobs)
            JOBS="$2"
            shift 2
            ;;
        --debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --release)
            BUILD_TYPE="Release"
            shift
            ;;
        --clean)
            CLEAN=1
            shift
            ;;
        --no-tests)
            RUN_TESTS=0
            shift
            ;;
        --gui)
            BUILD_DESKTOP_GUI=1
            shift
            ;;
        --no-cli)
            BUILD_CLI_COMPAT=0
            shift
            ;;
        --fetch-gui-deps)
            FETCH_GUI_DEPS=1
            shift
            ;;
        --imgui-dir)
            IMGUI_SOURCE_DIR="$2"
            shift 2
            ;;
        --glfw-dir)
            GLFW_SOURCE_DIR="$2"
            shift 2
            ;;
        --generator)
            CMAKE_GENERATOR="$2"
            shift 2
            ;;
        --)
            shift
            EXTRA_CMAKE_ARGS+=("$@")
            break
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Required command not found: $1" >&2
        exit 1
    fi
}

require_command cmake
require_command ctest

if [[ -n "${JOBS}" ]]; then
    EXTRA_BUILD_ARGS+=(--parallel "${JOBS}")
fi

CONFIGURE_ARGS=(
    -S "${ROOT_DIR}"
    -B "${BUILD_DIR}"
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
    -DBUILD_DESKTOP_GUI="${BUILD_DESKTOP_GUI}"
    -DBUILD_CLI_COMPAT="${BUILD_CLI_COMPAT}"
    -DTRADING_FETCH_GUI_DEPS="${FETCH_GUI_DEPS}"
)

if [[ -n "${CMAKE_GENERATOR}" ]]; then
    CONFIGURE_ARGS=(-G "${CMAKE_GENERATOR}" "${CONFIGURE_ARGS[@]}")
fi

if [[ -n "${IMGUI_SOURCE_DIR}" ]]; then
    CONFIGURE_ARGS+=(-DTRADING_IMGUI_SOURCE_DIR="${IMGUI_SOURCE_DIR}")
fi

if [[ -n "${GLFW_SOURCE_DIR}" ]]; then
    CONFIGURE_ARGS+=(-DTRADING_GLFW_SOURCE_DIR="${GLFW_SOURCE_DIR}")
fi

if [[ ${#EXTRA_CMAKE_ARGS[@]} -gt 0 ]]; then
    CONFIGURE_ARGS+=("${EXTRA_CMAKE_ARGS[@]}")
fi

if [[ "${CLEAN}" -eq 1 ]]; then
    echo "Cleaning ${BUILD_DIR}"
    rm -rf "${BUILD_DIR}"
fi

echo "Configuring ${BUILD_TYPE} build in ${BUILD_DIR}"
cmake "${CONFIGURE_ARGS[@]}"

echo "Building"
if [[ ${#EXTRA_BUILD_ARGS[@]} -gt 0 ]]; then
    cmake --build "${BUILD_DIR}" "${EXTRA_BUILD_ARGS[@]}"
else
    cmake --build "${BUILD_DIR}"
fi

if [[ "${RUN_TESTS}" -eq 1 ]]; then
    echo "Running tests"
    ctest --test-dir "${BUILD_DIR}" --output-on-failure
fi

echo "Build complete: ${BUILD_DIR}"
