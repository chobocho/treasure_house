#!/bin/sh
# pkg_diff.sh — 핀 고정한 pkg.in 이 이 기기의 pkg 와 같은가.
#
#   sh exp/pkg_diff.sh PKG.IN 설치된PKG 판
#
# termux-tools 의 스크립트는 @TERMUX_PREFIX@ 같은 자리표시를 품은
# .in 파일이다. 패키지를 지을 때 그 자리를 채운다. 여기서 같은 네
# 자리를 채워 설치본과 diff 하면, 남는 차이는 빌드가 따로 한 일뿐이다
# (6부). 판은 dpkg 가 적은 termux-tools 의 판을 넘긴다.
set -u
src=${1:?사용법: pkg_diff.sh PKG.IN 설치된PKG 판}
inst=${2:?}
ver=${3:?}
sed -e "s|@TERMUX_PREFIX@|$PREFIX|g" \
    -e "s|@TERMUX_APP_PACKAGE@|com.termux|g" \
    -e "s|@TERMUX_CACHE_DIR@|/data/data/com.termux/cache|g" \
    -e "s|@PACKAGE_VERSION@|$ver|g" "$src" | diff - "$inst"
echo "diff 종료 $?"
