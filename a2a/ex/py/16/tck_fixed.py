# TCK 의 세션 표지를 고정하는 pytest 플러그인 — 캡처가 실행마다 같게.
# TCK 는 작업·메시지 id 끝에 실행마다 다른 8자리(_SESSION, uuid4 의
# 앞 8자리)를 붙이고, 세 문 서버(13/doors*)는 받은 경로를 그대로
# 찍는다. 요구사항 표가 import 때 id 를 미리 지으므로, TCK 를 처음
# 불러오는 순간에만 uuid4 를 고정값으로 바꿔 둔다. 시험 내용은 같다.
#   run_tck.py … -- -p tck_fixed   (PYTHONPATH 에 ex/py/16)
import uuid

real = uuid.uuid4
uuid.uuid4 = lambda: uuid.UUID(int=0x16161616 << 96)
try:
    from tck.requirements import base
finally:
    uuid.uuid4 = real
assert base.tck_id("x") == "tck-x-16161616"
# @ norun
