#!/bin/sh
# build.sh — 파일 세 개로 .deb 하나 (실험 6).
#
#   sh exp/mkdeb/build.sh OUTDIR
#
# .deb 는 "DEBIAN/ 아래의 control·스크립트" 와 "설치될 경로 그대로의
# 파일" 을 묶은 것이다. Termux 패키지면 설치될 경로가
# /data/data/com.termux/files/usr/… 이다 — 그래서 준비 디렉터리 안에
# 그 경로를 통째로 만든다. 소유자는 root 로 적는다(--root-owner-group)
# — 만든 사람의 uid 가 패키지에 새지 않게.
set -eu
out=${1:?사용법: build.sh OUTDIR}
here=$(cd "$(dirname "$0")" && pwd)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
bin=$stage/data/data/com.termux/files/usr/bin
mkdir -p "$stage/DEBIAN" "$bin"
cp "$here/control" "$stage/DEBIAN/control"
cp "$here/postinst" "$stage/DEBIAN/postinst"
cp "$here/treasure-hello" "$bin/treasure-hello"
chmod 755 "$stage/DEBIAN/postinst" "$bin/treasure-hello"
mkdir -p "$out"
dpkg-deb --root-owner-group -Zxz --build "$stage" \
  "$out/treasure-hello_1.0_all.deb" > /dev/null
echo "$out/treasure-hello_1.0_all.deb"
