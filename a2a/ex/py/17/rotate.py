# 서명 키 교체 — 겹치는 동안 카드에 서명 둘, 키 저장소에 키 둘.
#   python 17/rotate.py
# 새 키 next-ed25519.pem 은 이 책의 시험 전용 키다(공개되어 있다).
import base64
import json
from pathlib import Path

from a2a.types import AgentCard
from a2a.utils.signing import (
    SignatureVerificationError,
    create_agent_card_signer,
    create_signature_verifier,
)
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
)
from jwt import PyJWK
from jwt.algorithms import OKPAlgorithm
from jwt.exceptions import PyJWKError

from workshop.fixtures import FIXTURES

PEM = {
    "settlement-2026": FIXTURES / "keys/settlement-ed25519.pem",
    "settlement-2027": Path(__file__).parent / "next-ed25519.pem",
}
OLD, NEW = PEM


def jwk(kid):  # 개인 키에서 공개 JWK 를 만든다
    pub = load_pem_private_key(PEM[kid].read_bytes(), None).public_key()
    return json.loads(OKPAlgorithm.to_jwk(pub)) | {"kid": kid}


# region: sign
def card(*kids):  # 같은 카드에 kid 마다 서명 하나씩
    c = AgentCard(name="보물상사 정산 에이전트", version="1.0.0")
    for kid in kids:
        head = {"alg": "EdDSA", "typ": "JOSE", "kid": kid}
        c = create_agent_card_signer(PEM[kid].read_bytes(), head)(c)
    return c


def store(*kids, strict=True):  # 클라이언트가 믿는 키 저장소
    keys = {k: PyJWK(jwk(k)) for k in kids}

    def provide(kid, jku):
        if kid not in keys:  # "이 서명은 틀림" — 다음 서명으로 넘어간다
            raise PyJWKError(f"모르는 kid {kid}")
        return keys[kid]

    def loose(kid, jku):
        return keys[kid]  # 모르는 kid 면 KeyError

    pick = provide if strict else loose
    return create_signature_verifier(pick, algorithms=["EdDSA"])


# endregion


def kid_of(sig):  # 보호 머리글(base64url JSON)의 kid
    raw = sig.protected + "=" * (-len(sig.protected) % 4)
    return json.loads(base64.urlsafe_b64decode(raw))["kid"]


def check(label, c, verify):
    try:
        verify(c)
        print(f"{label} → 맞음")
    except SignatureVerificationError as e:
        print(f"{label} → 틀림: {type(e).__name__}: {e}")
    except KeyError as e:
        print(f"{label} → 검증기 밖으로 KeyError: {e}")


# region: main
now, overlap, after = card(OLD), card(OLD, NEW), card(NEW)
print("겹침 동안 카드의 서명:", [kid_of(s) for s in overlap.signatures])
check("① 지금 — 옛 서명, 옛 키", now, store(OLD))
check("② 겹침 — 서명 둘, 옛 키만 아는 쪽", overlap, store(OLD))
check("② 겹침 — 서명 둘, 키 둘을 받은 쪽", overlap, store(OLD, NEW))
check("③ 겹침 뒤 — 새 서명, 옛 키만 아는 쪽", after, store(OLD))
check("③ 겹침 뒤 — 새 서명, 새 키", after, store(NEW))
check("④ 폐기 뒤 — 옛 카드를 다시 내밀면", now, store(NEW))
check("⑤ 키 공급자가 KeyError 를 내면", after, store(OLD, strict=False))
# 새 키부터 서명한 겹침 카드 — 고리는 서명을 적힌 차례로 대 본다
swapped = card(NEW, OLD)
print("새 키부터 서명한 카드:", [kid_of(s) for s in swapped.signatures])
check("⑥ 새 키 먼저, KeyError", swapped, store(OLD, strict=False))
check("⑦ 새 키 먼저, PyJWKError", swapped, store(OLD))
# endregion
