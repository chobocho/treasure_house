#!/bin/sh
# fetch_k8s_tools.sh — 2부에 필요한 도구와 스키마를 bin/ 에 받아 둔다.
#
# 이 저장소에는 클러스터가 없다. 그래서 2부는 "띄워 보는" 대신
# **읽고 검증하는** 것으로 배운다. 그 두 가지에 필요한 것이 여기 있다.
#
#   kubectl      매니페스트를 합친다(kubectl kustomize). 오프라인으로 된다.
#   kubeconform  매니페스트가 규격에 맞는지 검사한다.
#   스키마       쿠버네티스가 공개한 JSON 스키마. 필드 설명이 여기서 나온다.
#
# 받은 것의 판번호와 sha256 은 deck/claims.md 에 적혀 있다.
# bin/ 는 .gitignore 에 있다 — 크고, 다시 받을 수 있기 때문이다.
set -eu
cd "$(dirname "$0")/.."

BIN=bin
SCHEMAS=$BIN/schemas
mkdir -p "$SCHEMAS"

# 스키마는 kubeconform 이 기본으로 보는 그 저장소에서 받는다.
# -standalone-strict = 파일 하나로 완결되고, 모르는 필드를 거절하는 판.
BASE=https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master
SET=master-standalone-strict

say() { printf '  %s\n' "$1"; }

if [ ! -x "$BIN/kubectl" ]; then
  V=$(curl -sS https://dl.k8s.io/release/stable.txt)
  say "kubectl $V 내려받는 중"
  curl -sSL -o "$BIN/kubectl" \
    "https://dl.k8s.io/release/$V/bin/linux/arm64/kubectl"
  curl -sSL -o "$BIN/kubectl.sha256" \
    "https://dl.k8s.io/release/$V/bin/linux/arm64/kubectl.sha256"
  echo "$(cat "$BIN/kubectl.sha256")  $BIN/kubectl" | sha256sum -c -
  chmod +x "$BIN/kubectl"
fi

if [ ! -x "$BIN/kubeconform" ]; then
  say 'kubeconform 내려받는 중'
  V=$(curl -sS https://api.github.com/repos/yannh/kubeconform/releases/latest \
      | python3 -c 'import json,sys;print(json.load(sys.stdin)["tag_name"])')
  curl -sSL -o "$BIN/kubeconform.tgz" \
    "https://github.com/yannh/kubeconform/releases/download/$V/kubeconform-linux-arm64.tar.gz"
  tar xzf "$BIN/kubeconform.tgz" -C "$BIN" kubeconform
  chmod +x "$BIN/kubeconform"
  rm -f "$BIN/kubeconform.tgz"
fi

for f in namespace-v1 deployment-apps-v1 service-v1 ingress-networking-v1 \
         configmap-v1 secret-v1 pod-v1; do
  [ -f "$SCHEMAS/$f.json" ] && continue
  say "스키마 $f"
  curl -sSL -o "$SCHEMAS/$f.json" "$BASE/$SET/$f.json"
done

echo '준비됨:'
"$BIN/kubectl" version --client | sed 's/^/  /'
printf '  kubeconform %s\n' "$("$BIN/kubeconform" -v)"
printf '  스키마 %s개 (%s)\n' "$(ls "$SCHEMAS" | wc -l)" "$SET"
