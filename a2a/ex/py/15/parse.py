# 기획 에이전트가 쓰는 문장 풀이(workshop.domain.parse_request)를
# 일곱 문장에 돌린다. 세 언어가 같은 줄을 찍어야 한다.
import json

from workshop.domain import parse_request

CASES = [
    "2026-10-30부터 1박 2일, 30명(채식 2명), 예산 6,000,000원",
    "채식 2명 포함 30명, 2026-11-06 1박",
    # 1장의 대화 셋을 기획 에이전트가 이어 붙인 꼴
    "1박 2일, 30명(채식 2명) 2026-10-30부터 예산 6,000,000원",
    "2026-10-30 1박 30명, 아니 40명",
    "2026-10-30 1박 ３０명",  # 전각 숫자
    "다음 주에 워크숍 가고 싶어요",
    # 1장 끝 — TS 기획 에이전트가 푸는 꼴(이번 메시지가 두 번)
    "2026-10-30 1박, 채식 2명 2026-10-30 1박, 채식 2명",
]
for text in CASES:
    got = parse_request(text)
    print(text)
    print(
        "  →",
        json.dumps(
            got,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
