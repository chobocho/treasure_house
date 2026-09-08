"""도구 등록기 — 9건."""
import unittest
from typing import Optional

from mini_puppy.tools import ToolError, ToolRegistry, coerce


class CoerceTest(unittest.TestCase):
    def test_문자열_숫자를_정수로(self):
        self.assertEqual(coerce("42", int), 42)
        self.assertEqual(coerce(" 7 ", int), 7)

    def test_문자열_참거짓(self):
        for 참 in ("true", "TRUE", "yes", "1", "on"):
            self.assertIs(coerce(참, bool), True)
        for 거짓 in ("false", "no", "0", "off"):
            self.assertIs(coerce(거짓, bool), False)

    def test_못_바꾸면_ToolError(self):
        with self.assertRaises(ToolError):
            coerce("사과", int)
        with self.assertRaises(ToolError):
            coerce("아마도", bool)

    def test_Optional_은_안쪽_타입으로_본다(self):
        self.assertEqual(coerce("3", Optional[int]), 3)
        self.assertIsNone(coerce(None, Optional[int]))

    def test_JSON_문자열을_dict_로(self):
        self.assertEqual(coerce('{"a": 1}', dict), {"a": 1})
        with self.assertRaises(ToolError):
            coerce("{안 닫힘", dict)


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self.reg = ToolRegistry()

        @self.reg.register
        def 더하기(a: int, b: int = 1) -> int:
            """두 수를 더한다.

            Args:
              a: 첫 수
              b: 둘째 수
            """
            return a + b

        @self.reg.register(name="터짐")
        def boom() -> str:
            """일부러 터진다."""
            raise ValueError("안에서 터졌다")

    def test_스키마를_서명에서_뽑는다(self):
        s = self.reg.schemas()[0]
        self.assertEqual(s["name"], "더하기")
        self.assertEqual(s["description"], "두 수를 더한다.")
        self.assertEqual(s["parameters"]["properties"]["a"]["type"], "integer")
        self.assertEqual(s["parameters"]["properties"]["a"]["description"], "첫 수")
        self.assertEqual(s["parameters"]["required"], ["a"])

    def test_허용_목록_밖은_스키마에도_없고_불러도_거부된다(self):
        allow = ["터짐"]
        self.assertEqual([s["name"] for s in self.reg.schemas(allow)], ["터짐"])
        out = self.reg.call("더하기", {"a": 1}, allowlist=allow)
        self.assertFalse(out.ok)
        self.assertIn("도구가 없다", out.content)

    def test_도구가_터져도_예외가_새지_않는다(self):
        out = self.reg.call("터짐", {})
        self.assertFalse(out.ok)
        self.assertIn("ValueError", out.content)

    def test_긴_출력은_가운데를_자른다(self):
        @self.reg.register
        def 수다() -> str:
            """길게 떠든다."""
            return "가" * 5000

        out = self.reg.call("수다", {}, max_output=1000)
        self.assertTrue(out.ok)
        self.assertTrue(out.truncated)
        self.assertLess(len(out.content), 1200)
        self.assertIn("자 잘림", out.content)


if __name__ == "__main__":
    unittest.main()
