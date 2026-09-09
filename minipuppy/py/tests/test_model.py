"""모델 층과 라운드로빈 — 11건."""
import unittest

from mini_puppy.factory import ModelConfigError, build_model, load_models
from mini_puppy.model import (HTTPModel, ModelError, ModelReply,
                              RoundRobinModel, ScriptedModel)


class 시계:
    """가짜 단조 시계. 쿨다운을 실제로 기다리지 않고 시험한다."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def 흘려보내기(self, 초):
        self.now += 초


def 모델(name, 터짐=False, retryable=True):
    class M:
        def __init__(self):
            self.name = name
            self.count = 0

        def complete(self, messages, tools):
            self.count += 1
            if 터짐:
                raise ModelError("%s 실패" % name, retryable=retryable)
            return ModelReply(text=name, model=name)

    return M()


class RoundRobinTest(unittest.TestCase):
    def test_rotate_every_만큼_같은_모델을_쓴다(self):
        rr = RoundRobinModel("rr", [모델("a"), 모델("b"), 모델("c")],
                             rotate_every=2)
        for _ in range(6):
            rr.complete([], [])
        self.assertEqual(rr.picks, ["a", "a", "b", "b", "c", "c"])

    def test_rotate_every_1_은_매번_바꾼다(self):
        rr = RoundRobinModel("rr", [모델("a"), 모델("b")], rotate_every=1)
        for _ in range(4):
            rr.complete([], [])
        self.assertEqual(rr.picks, ["a", "b", "a", "b"])

    def test_실패한_모델은_쿨다운_동안_건너뛴다(self):
        clock = 시계()
        a, b = 모델("a", 터짐=True), 모델("b")
        rr = RoundRobinModel("rr", [a, b], rotate_every=1, cooldown=30.0,
                             clock=clock)
        with self.assertRaises(ModelError):
            rr.complete([], [])                      # a 가 터진다
        self.assertEqual(rr.complete([], []).text, "b")
        self.assertEqual(rr.complete([], []).text, "b")   # a 는 아직 쉬는 중
        self.assertEqual(a.count, 1)                 # a 를 다시 안 불렀다
        clock.흘려보내기(31)                          # 쿨다운이 끝나면
        self.assertTrue(rr._healthy(a))              # 다시 후보가 된다
        for _ in range(2):
            try:
                rr.complete([], [])
            except ModelError:
                pass
        self.assertEqual(a.count, 2)                 # 한 바퀴 돌아 a 가 다시 나왔다

    def test_다시_걸_수_없는_오류는_쿨다운을_안_건다(self):
        clock = 시계()
        rr = RoundRobinModel("rr", [모델("a", 터짐=True, retryable=False),
                                    모델("b")], rotate_every=1, clock=clock)
        with self.assertRaises(ModelError):
            rr.complete([], [])
        self.assertEqual(rr.down, {})    # 우리 잘못은 다른 모델로 돌려도 똑같다

    def test_모델이_없으면_만들_수_없다(self):
        with self.assertRaises(ValueError):
            RoundRobinModel("rr", [])


class ParseTest(unittest.TestCase):
    def test_도구_호출을_읽는다(self):
        m = HTTPModel("t", url="http://x")
        got = m.parse({"choices": [{"message": {
            "content": None,
            "tool_calls": [{"id": "c1", "function": {
                "name": "read_file", "arguments": '{"path": "a.py"}'}}]}}],
            "usage": {"total_tokens": 12}})
        self.assertTrue(got.wants_tools)
        self.assertEqual(got.tool_calls[0].name, "read_file")
        self.assertEqual(got.tool_calls[0].args, {"path": "a.py"})
        self.assertEqual(got.usage["total_tokens"], 12)

    def test_깨진_인자_JSON_도_삼킨다(self):
        m = HTTPModel("t", url="http://x")
        got = m.parse({"choices": [{"message": {"tool_calls": [
            {"id": "c1", "function": {"name": "grep",
                                      "arguments": '{"needle": '}}]}}]})
        self.assertIn("__raw", got.tool_calls[0].args)


class FactoryTest(unittest.TestCase):
    DEFS = {
        "빠름": {"type": "openai", "url": "https://api.x/v1",
                 "model_id": "gpt-4.1", "api_key": "$MY_KEY"},
        "느림": {"type": "openai", "url": "https://api.y/v1"},
        "교대": {"type": "round_robin", "models": ["빠름", "느림"],
                 "rotate_every": 4},
        "자기참조": {"type": "round_robin", "models": ["자기참조"]},
    }

    def test_round_robin_은_모델의_한_종류다(self):
        got = build_model("교대", self.DEFS, environ={})
        self.assertIsInstance(got, RoundRobinModel)
        self.assertEqual(got.rotate_every, 4)
        self.assertTrue(hasattr(got, "complete"))    # 규약이 같다

    def test_api_key_는_환경변수에서_푼다(self):
        got = build_model("빠름", self.DEFS, environ={"MY_KEY": "sk-비밀"})
        self.assertEqual(got.api_key, "sk-비밀")
        self.assertEqual(build_model("빠름", self.DEFS, environ={}).api_key, "")

    def test_자기를_가리키면_막는다(self):
        with self.assertRaises(ModelConfigError) as cm:
            build_model("자기참조", self.DEFS, environ={})
        self.assertIn("자기 자신", str(cm.exception))

    def test_없는_이름은_있는_것을_알려_준다(self):
        with self.assertRaises(ModelConfigError) as cm:
            build_model("없음", self.DEFS, environ={})
        self.assertIn("빠름", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
