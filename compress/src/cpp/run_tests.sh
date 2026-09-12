#!/bin/sh
# C++ 시험을 짓고 돌린다. 바깥 라이브러리를 안 쓰므로 컴파일 한 번이 전부다.
#
#     sh src/cpp/run_tests.sh
#
# -Werror 를 켜 둔다. C++ 에서 파서티가 깨지는 자리는 거의 늘 정수 승격이고,
# 경고 가운데 몇은 그것을 미리 잡아 준다 (전부는 못 잡는다 — SPEC §0.5).
set -e
HERE=$(dirname "$0")
BUILD="$HERE/../../build"
mkdir -p "$BUILD"
g++ -std=c++20 -O2 -Wall -Wextra -Werror \
    -o "$BUILD/cpptests" "$HERE/tests/test_all.cpp"
"$BUILD/cpptests"
