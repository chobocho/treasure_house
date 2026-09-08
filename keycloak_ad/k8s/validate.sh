#!/bin/sh
# validate.sh — 매니페스트가 규격에 맞는지 검사한다.
#
# 이 저장소에는 클러스터가 없다. 그래도 할 수 있는 검사가 있다 —
# **쿠버네티스가 공개한 JSON 스키마와 맞춰 보는 것**이다.
# 오타 난 필드, 빠진 필수 항목, 틀린 타입이 여기서 전부 걸린다.
#
# 못 잡는 것도 분명히 있다. 이미지가 진짜 있는지, 셀렉터가 실제로
# 어떤 Pod 를 고르는지, 자원이 클러스터에 남아 있는지는 못 본다.
# 그래서 이 검사는 tier B(구문 검증)이지 tier A 가 아니다.
#
#   sh k8s/validate.sh
set -eu
cd "$(dirname "$0")/.."

KUBECTL=bin/kubectl
CONFORM=bin/kubeconform
KVER=1.37.0

for t in "$KUBECTL" "$CONFORM"; do
  [ -x "$t" ] || {
    echo "$t 이 없다 — sh tools/fetch_k8s_tools.sh 를 먼저 돌릴 것" >&2
    exit 1
  }
done

# -strict = 스키마에 없는 필드를 오류로 본다.
#   이게 없으면 replicas 를 replica 로 잘못 적어도 조용히 지나간다.
# -summary = 한 줄로 줄여 준다.
conform() {
  "$CONFORM" -strict -summary -kubernetes-version "$KVER" \
    -cache bin/.kccache -
}

echo "kubectl    $("$KUBECTL" version --client -o yaml \
  | sed -n 's/^  gitVersion: //p' | head -1)"
echo "kubeconform $("$CONFORM" -v)"
echo "스키마     쿠버네티스 $KVER"
echo

for dir in k8s/base k8s/overlays/dev k8s/overlays/prod; do
  echo "$dir"
  "$KUBECTL" kustomize "$dir" | conform | sed 's/^/  /'
done
