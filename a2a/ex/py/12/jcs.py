# 정산 카드의 서명을 손으로 풀어 본다 — 보호 헤더, JCS 로 정규화한
# 카드, 서명할 입력, 그리고 Ed25519 로 직접 확인.
#   python 12/jcs.py 에이전트주소
import json
import sys

import httpx
from a2a.client.card_resolver import parse_agent_card
from a2a.utils.signing import _canonicalize_agent_card
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from jwt.utils import base64url_decode, base64url_encode

from workshop.fixtures import FIXTURES

url = sys.argv[1]
raw = httpx.get(url + ".well-known/agent-card.json").json()

# region: main
card = parse_agent_card(raw)
sig = card.signatures[0]
header = base64url_decode(sig.protected.encode()).decode()
print(f"① 보호 헤더: {header}")
# SDK 의 비공개 함수 — 서명기와 검증기가 쓰는 바로 그 정규화
payload = _canonicalize_agent_card(card).encode()
print(f"② 정규화한 카드: {len(payload)}바이트, 앞부분")
text = payload.decode()
for i in range(0, 240, 80):
    print(f"   {text[i : i + 80]}")
print(f"   첫 단계 키: {', '.join(json.loads(payload))}")
signing_input = sig.protected + "." + base64url_encode(payload).decode()
print(f"③ 서명할 입력: 보호 헤더 . 카드 = {len(signing_input)}글자")
signature = base64url_decode(sig.signature.encode())
jwks = json.loads((FIXTURES / "keys/jwks.json").read_text())
x = base64url_decode(jwks["keys"][0]["x"].encode())
public = Ed25519PublicKey.from_public_bytes(x)
public.verify(signature, signing_input.encode())  # 틀리면 예외
print(f"④ 서명 {len(signature)}바이트 — 공개 키로 직접 확인: 맞음")
# endregion
# @ norun
