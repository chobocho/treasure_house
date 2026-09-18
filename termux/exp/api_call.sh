#!/bin/sh
# api_call.sh — termux-battery-status 는 무엇을 부르나 (실험 7).
#
# termux-* 명령 대부분은 몇 줄짜리 셸 스크립트다. 인자를 검사한 뒤
# $PREFIX/libexec/termux-api 에 **메서드 이름 하나** 를 넘긴다.
# termux-api 는 그 이름을 Termux:API 앱에 보내고, 앱이 JSON 을
# 돌려준다(7부). 여기서는 설치된 스크립트에서 그 줄을 읽어 이름을
# 뽑고, termux-api 를 직접 불러 같은 답이 오는지 본다.
# TERMUX_API 로 부를 실행 파일을 바꿀 수 있다(시험용).
set -eu
bs=$(command -v termux-battery-status)
line=$(grep -m1 'libexec/termux-api ' "$bs")
method=${line##*termux-api }
api=${TERMUX_API:-${line%% *}}
echo "스크립트: $bs"
echo "메서드 이름: $method"
"$api" "$method"
