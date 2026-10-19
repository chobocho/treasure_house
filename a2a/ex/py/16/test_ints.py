# 정수 자리 손질(as_ints) 시험 — 수로 읽을 수 없는 값은 0 이 되어
# 업무 규칙이 거절해야 한다. Go 의 common.Int 와 같은 약속이다.
#   python 16/test_ints.py        고친 agents/common.py
#   python 16/test_ints.py old    고치기 전 판(16/ints_old.py)
import io
import re
import sys
import unittest

from workshop import domain

if sys.argv[1:] == ["old"]:
    from ints_old import as_ints
else:
    from agents.common import as_ints
del sys.argv[1:]

BAD = {"date": "2026-10-30", "nights": 1, "headcount": "서른"}
BAD_SIZE = "인원과 박 수는 1 이상이어야 합니다"  # SCENARIO §2.7


# region: tests
class IntsTest(unittest.TestCase):
    def test_numbers_come_back_as_ints(self):
        got = as_ints(
            {"nights": 1.0, "headcount": "30"}, "nights", "headcount"
        )
        self.assertEqual(got, {"nights": 1, "headcount": 30})

    def test_not_a_number_is_zero(self):
        got = as_ints(BAD, "nights", "headcount")
        self.assertEqual(got["headcount"], 0)

    def test_lodging_rejects_it(self):
        quote = domain.choose_lodging(
            as_ints(BAD, "nights", "headcount")
        )
        self.assertEqual(quote, {"ok": False, "reason": BAD_SIZE})


# endregion


class NoClock(io.TextIOBase):
    """'Ran 3 tests in 0.001s' 의 시간만 가린다(실행마다 달라서)."""

    def write(self, s):
        return sys.stdout.write(re.sub(r"in \d+\.\d+s$", "in <초>", s))


if __name__ == "__main__":
    runner = unittest.TextTestRunner(stream=NoClock(), verbosity=2)
    unittest.main(testRunner=runner)
# @ norun
