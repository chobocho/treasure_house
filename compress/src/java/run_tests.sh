#!/bin/sh
# 자바 시험을 짓고 돌린다. JUnit 도 Maven 도 안 쓴다 — main 하나다.
#
#     sh tools/flock_java.sh sh src/java/run_tests.sh
#
# **반드시 flock 을 통해 부를 것.** 이 기계는 JVM 을 한 번에 하나만
# 띄울 수 있고, 둘이 겹치면 세션째 OOM 으로 죽는다.
set -e
HERE=$(dirname "$0")
BASE="$HERE/../.."
BUILD="$BASE/build/java"
mkdir -p "$BUILD"
javac -d "$BUILD" $(find "$BASE/src/java" "$BASE/cli/java" -name '*.java')
java -cp "$BUILD" compresslib.RunTests
