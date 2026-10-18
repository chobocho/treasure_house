# 정산 카드의 서명을 SDK 로 검증한다 — 진짜 카드, 고친 카드 둘,
# 가짜 카드를 미리 받아 둔 키로, 마지막엔 가짜 카드의 jku 를 따라가서.
#   python 12/verify.py 진짜주소 가짜주소
import copy
import json
import sys

import httpx
from a2a.client.card_resolver import parse_agent_card
from a2a.utils.signing import (
    SignatureVerificationError,
    create_signature_verifier,
)
from jwt import PyJWK

from workshop.fixtures import FIXTURES

REAL, FAKE = sys.argv[1:3]


def card_json(url):
    return httpx.get(url + ".well-known/agent-card.json").json()


# region: verifiers
# 미리 받아 둔 공개 키(ex/fixtures/keys/jwks.json)만 믿는다
jwks = json.loads((FIXTURES / "keys/jwks.json").read_text())
keys = {k["kid"]: PyJWK(k) for k in jwks["keys"]}
pinned = create_signature_verifier(
    lambda kid, jku: keys[kid], algorithms=["EdDSA"]
)


def from_jku(kid, jku):  # 카드가 가리키는 JWKS 를 그대로 믿는다
    got = httpx.get(jku).json()["keys"]
    return PyJWK(next(k for k in got if k["kid"] == kid))


trusting = create_signature_verifier(from_jku, algorithms=["EdDSA"])
# endregion


# region: main
def check(label, raw, verify):
    try:
        verify(parse_agent_card(raw))
        print(f"{label} → 맞음")
    except SignatureVerificationError as e:
        print(f"{label} → 틀림: {type(e).__name__}: {e}")


real, fake = card_json(REAL), card_json(FAKE)
moved = copy.deepcopy(real)
flows = moved["securitySchemes"]["oauth"]["oauth2SecurityScheme"]
flows["flows"]["clientCredentials"]["tokenUrl"] = FAKE + "oauth/token"
check("① 진짜 카드", real, pinned)
check("② tokenUrl 을 바꾼 진짜 카드", moved, pinned)
check(
    "③ 모르는 필드를 더한 진짜 카드", real | {"note": "덧붙임"}, pinned
)
check("④ 가짜 카드", fake, pinned)
check("⑤ 가짜 카드, jku 를 따라가면", fake, trusting)
# endregion
# @ norun
