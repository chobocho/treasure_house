"""시나리오 자료(ex/fixtures/*.json)를 읽는다.

세 언어가 같은 파일을 쓴다.
"""

import json
from functools import cache
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


@cache
def workshop():
    """숙소·메뉴·버스·결재 기준. 한 번 읽어 두고 계속 쓴다."""
    path = FIXTURES / "workshop.json"
    return json.loads(path.read_text(encoding="utf-8"))


@cache
def clients():
    """로컬 OAuth2 발급기가 아는 클라이언트 목록."""
    path = FIXTURES / "clients.json"
    return json.loads(path.read_text(encoding="utf-8"))["clients"]
