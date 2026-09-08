"""실행 루프 — 9건. 루프가 어떤 상황에서도 안 죽는지 본다."""
from mini_puppy.agent import Agent, CancelToken, to_wire
from mini_puppy.model import ModelError, ModelReply

from .helpers import TempCase, call, reply, scripted


class 터지는모델:
    name = "터짐"

    def complete(self, messages, tools):
        raise ModelError("502 Bad Gateway", retryable=True)


class 무한모델:
    """끝없이 같은 도구만 부른다. 걸음 제한이 없으면 영원히 돈다."""
    name = "무한"

    def __init__(self):
        self.count = 0

    def complete(self, messages, tools):
        self.count += 1
        return reply("", call("list_files"))


class AgentTest(TempCase):
    def setUp(self):
        super().setUp()
        self.write("a.py", "x = 1\n")
        self.reg = self.registry()

    def agent(self, model, tools=None, bus=None, config=None):
        return Agent("t", "너는 시험용이다.", model, self.reg, tools=tools,
                     bus=bus, config=config)

    def test_도구를_안_부르면_한_걸음에_끝난다(self):
        result, hist = self.agent(scripted("다 했다")).run("안녕",
                                                          ctx=self.workspace())
        self.assertEqual(result.text, "다 했다")
        self.assertEqual(result.steps, 1)
        self.assertEqual(result.tool_calls, 0)
        self.assertEqual(result.stopped, "done")
        self.assertEqual([m.role for m in hist.messages],
                         ["system", "user", "assistant"])

    def test_도구를_부르면_결과를_붙이고_다시_묻는다(self):
        model = scripted(reply("", call("read_file", path="a.py")),
                         "파일은 x = 1 이다")
        result, hist = self.agent(model).run("a.py 보여줘", ctx=self.workspace())
        self.assertEqual(result.steps, 2)
        self.assertEqual(result.tool_calls, 1)
        self.assertEqual(result.text, "파일은 x = 1 이다")
        roles = [m.role for m in hist.messages]
        self.assertEqual(roles, ["system", "user", "assistant", "tool",
                                 "assistant"])
        self.assertIn("x = 1", hist.messages[3].content)
        # 두 번째 호출 때 모델은 도구 결과를 봤다
        self.assertEqual(model.calls[1]["messages"][-1]["role"], "tool")

    def test_도구가_실패해도_모델에게_돌려주고_계속한다(self):
        model = scripted(reply("", call("read_file", path="없는파일.py")),
                         "없다고 하네. 다른 걸 보자")
        result, hist = self.agent(model).run("보여줘", ctx=self.workspace())
        self.assertEqual(result.stopped, "done")
        self.assertIn("오류", hist.messages[3].content)
        self.assertEqual(result.text, "없다고 하네. 다른 걸 보자")

    def test_걸음_제한이_무한_루프를_끊는다(self):
        model = 무한모델()
        result, _h = self.agent(model).run("돌아라", ctx=self.workspace(),
                                           max_steps=5)
        self.assertEqual(result.stopped, "max_steps")
        self.assertEqual(result.steps, 5)
        self.assertEqual(model.count, 5)

    def test_모델이_터지면_루프가_깨끗하게_멈춘다(self):
        result, _h = self.agent(터지는모델()).run("안녕", ctx=self.workspace())
        self.assertEqual(result.stopped, "model_error")
        self.assertIn("502", result.error)

    def test_취소_신호는_걸음_사이에서_듣는다(self):
        token = CancelToken()
        token.cancel()
        result, _h = self.agent(scripted("올게")).run("가라",
                                                      ctx=self.workspace(),
                                                      cancel=token)
        self.assertEqual(result.stopped, "cancelled")
        self.assertEqual(result.tool_calls, 0)

    def test_허용_목록_밖의_도구를_부르면_거절이_돌아간다(self):
        model = scripted(reply("", call("write_file", path="새것", content="x")),
                         "못 쓰는구나")
        result, hist = self.agent(model, tools=["read_file"]).run(
            "파일 만들어", ctx=self.workspace())
        self.assertIn("도구가 없다", hist.messages[3].content)
        self.assertFalse((self.tmp / "새것").exists())
        self.assertEqual(result.stopped, "done")

    def test_창이_넘치면_스스로_접는다(self):
        self.write("큰파일.py", ("# 아주 긴 주석 한 줄이다" + chr(10)) * 400)
        모델대본 = [reply("", call("read_file", path="큰파일.py"))
                    for _ in range(6)]
        모델대본.append("끝")
        cfg = self.config(context_window="400", compaction_threshold="0.5",
                          protected_tokens="100")
        result, hist = self.agent(scripted(*모델대본), config=cfg).run(
            "여러 번 읽어", ctx=self.workspace(), max_steps=10)
        self.assertGreater(result.compactions, 0)
        self.assertEqual(hist.messages[0].role, "system")

    def test_버스에_사건이_흐른다(self):
        bus, sink = self.bus()
        model = scripted(reply("", call("list_files")), "봤다")
        self.agent(model, bus=bus).run("목록", ctx=self.workspace())
        kinds = [m.kind for m in sink.messages]
        self.assertEqual(kinds[0], "user")
        self.assertIn("tool", kinds)
        self.assertIn("tool_out", kinds)
        self.assertEqual(kinds[-1], "agent")


class WireTest(TempCase):
    def test_도구_호출과_결과가_API_모양으로_나간다(self):
        from mini_puppy.history import History
        h = History("시스템")
        h.user("해봐")
        h.assistant("", tool_name="grep", tool_call_id="c1",
                    tool_args={"needle": "x"})
        h.tool_result("c1", "grep", "a.py:1: x")
        wire = to_wire(h)
        self.assertEqual(wire[2]["tool_calls"][0]["function"]["name"], "grep")
        self.assertEqual(wire[3]["role"], "tool")
        self.assertEqual(wire[3]["tool_call_id"], "c1")
