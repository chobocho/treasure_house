"""대화 기록과 컴팩션 — 13건. 이 파일이 mini-puppy 에서 가장 중요하다."""
import unittest

from mini_puppy.history import (History, Message, default_summarizer,
                                estimate_tokens)


class TokenTest(unittest.TestCase):
    def test_빈_문자열은_0(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_한글이_영어보다_비싸다(self):
        영어 = estimate_tokens("a" * 60)
        한글 = estimate_tokens("가" * 60)
        self.assertGreater(한글, 영어)

    def test_길이에_비례한다(self):
        짧 = estimate_tokens("hello " * 10)
        긺 = estimate_tokens("hello " * 100)
        self.assertGreater(긺, 짧 * 5)


class HistoryTest(unittest.TestCase):
    def build(self, turns=12):
        h = History("너는 코딩 에이전트다.")
        for i in range(turns):
            h.user("요청 %d — %s" % (i, "긴 문장을 채운다 " * 12))
            h.assistant("", tool_name="read_file", tool_call_id="c%d" % i,
                        tool_args={"path": "a.py"})
            h.tool_result("c%d" % i, "read_file", "파일 내용 " * 40)
        return h

    def test_역할이_틀리면_거부한다(self):
        with self.assertRaises(ValueError):
            Message("사장님", "안녕")

    def test_임계를_넘으면_컴팩션이_필요하다고_한다(self):
        h = self.build()
        self.assertTrue(h.needs_compaction(window=2000, threshold=0.75))
        self.assertFalse(h.needs_compaction(window=10 ** 6, threshold=0.75))

    def test_시스템_프롬프트는_살아남는다(self):
        h = self.build()
        h.compact(protected_tokens=200)
        self.assertEqual(h.messages[0].role, "system")
        self.assertIn("코딩 에이전트", h.messages[0].content)

    def test_최근_구간은_안_지운다(self):
        h = self.build()
        마지막 = h.messages[-1].content
        h.compact(protected_tokens=400)
        self.assertEqual(h.messages[-1].content, 마지막)

    def test_접으면_토큰이_준다(self):
        h = self.build()
        before = h.total_tokens()
        got = h.compact(protected_tokens=300)
        self.assertIsNotNone(got)
        self.assertLess(h.total_tokens(), before)

    def test_도구_결과만_홀로_남지_않는다(self):
        """컴팩션의 진짜 함정 — assistant(tool_call) 없이 tool 결과가 남으면
        모델 API 가 400 을 던진다. 경계를 앞으로 당겨 짝을 통째로 지킨다."""
        h = self.build()
        for protected in (50, 120, 300, 700, 1500):
            copy = History.from_list(h.to_list())
            copy.compact(protected_tokens=protected)
            열린_호출 = set()
            for m in copy.messages:
                if m.role == "assistant" and m.tool_call_id:
                    열린_호출.add(m.tool_call_id)
                elif m.role == "tool":
                    self.assertIn(m.tool_call_id, 열린_호출,
                                  "짝 없는 도구 결과가 남았다 (protected=%d)"
                                  % protected)

    def test_접을_중간이_없으면_None(self):
        h = History("시스템")
        h.user("한 마디")
        self.assertIsNone(h.compact(protected_tokens=10000))

    def test_요약이_무엇을_했는지_적는다(self):
        h = self.build(6)
        got = h.compact(protected_tokens=200)
        self.assertIsNotNone(got)
        _n, summary = got
        self.assertIn("read_file", summary)
        self.assertIn("[요약]", summary)

    def test_두_번_접어도_안전하다(self):
        h = self.build()
        h.compact(protected_tokens=300)
        h.compact(protected_tokens=300)
        self.assertEqual(h.messages[0].role, "system")
        self.assertGreater(len(h), 1)

    def test_직렬화_왕복(self):
        h = self.build(3)
        back = History.from_list(h.to_list())
        self.assertEqual(len(back), len(h))
        self.assertEqual(back.messages[2].tool_args, {"path": "a.py"})
        self.assertEqual(back.total_tokens(), h.total_tokens())


if __name__ == "__main__":
    unittest.main()
