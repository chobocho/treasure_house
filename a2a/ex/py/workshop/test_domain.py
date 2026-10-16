"""골든 벡터 시험 — ex/fixtures/golden/domain.json 의 기대값과 한 글자도
다르면 안 된다. 같은 파일을 TypeScript·Go 시험도 읽는다."""

import json
import unittest
from pathlib import Path

from workshop import domain

GOLDEN = (
    Path(__file__).resolve().parents[2] / "fixtures/golden/domain.json"
)
CASES = json.loads(GOLDEN.read_text(encoding="utf-8"))


# 골든 파일의 키는 언어 중립(camelCase), 파이썬 함수는 snake_case.
FUNCS = {
    "chooseLodging": domain.choose_lodging,
    "planMeals": domain.plan_meals,
    "chooseBuses": domain.choose_buses,
    "settle": domain.settle,
    "parseRequest": domain.parse_request,
}


class GoldenTest(unittest.TestCase):
    def check(self, fn_name):
        fn = FUNCS[fn_name]
        for case in CASES[fn_name]:
            with self.subTest(case=case["name"]):
                self.assertEqual(fn(case["input"]), case["expected"])

    def test_choose_lodging(self):
        self.check("chooseLodging")

    def test_plan_meals(self):
        self.check("planMeals")

    def test_choose_buses(self):
        self.check("chooseBuses")

    def test_settle(self):
        self.check("settle")

    def test_parse_request(self):
        self.check("parseRequest")


if __name__ == "__main__":
    unittest.main()
