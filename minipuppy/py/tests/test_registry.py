"""에이전트 등록기와 서브에이전트 — 11건."""
import json

from mini_puppy.agent import Agent
from mini_puppy.registry import (AgentRegistry, AgentSpec,
                                 register_subagent_tool)

from .helpers import TempCase, call, reply, scripted


class RegistryTest(TempCase):
    def agents_dir(self):
        d = self.tmp / "agents"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def json_agent(self, name, **body):
        body.setdefault("name", name)
        (self.agents_dir() / (name + ".json")).write_text(
            json.dumps(body, ensure_ascii=False), encoding="utf-8")

    def test_내장_에이전트가_들어_있다(self):
        reg = AgentRegistry(None)
        self.assertIn("mini-puppy", reg.names())
        self.assertIn("reader", reg.names())
        self.assertIsNone(reg.get("없는놈"))

    def test_reader_에는_쓰기_도구가_없다(self):
        reg = AgentRegistry(None)
        tools = reg.get("reader").tools
        for 금지 in ("write_file", "edit_file", "run_command"):
            self.assertNotIn(금지, tools)

    def test_JSON_파일_하나로_새_인격이_생긴다(self):
        self.json_agent("python-tutor",
                        display_name="Python Tutor 🐍",
                        system_prompt=["너는 파이썬 튜터다.", "답을 바로 주지 마라."],
                        tools=["read_file", "grep"])
        reg = AgentRegistry(self.agents_dir())
        spec = reg.get("python-tutor")
        self.assertEqual(spec.display_name, "Python Tutor 🐍")
        self.assertIn("답을 바로 주지 마라", spec.system_prompt)
        self.assertEqual(spec.tools, ["read_file", "grep"])
        self.assertNotEqual(spec.source, "builtin")

    def test_파일이_같은_이름의_내장을_덮는다(self):
        self.json_agent("reader", system_prompt="바꿔치기", tools=["grep"])
        reg = AgentRegistry(self.agents_dir())
        self.assertEqual(reg.get("reader").tools, ["grep"])

    def test_이름_규칙을_어기면_오류_목록에_남고_나머지는_산다(self):
        (self.agents_dir() / "나쁜이름.json").write_text(
            json.dumps({"name": "한글 이름!!"}, ensure_ascii=False),
            encoding="utf-8")
        self.json_agent("good-one", tools=["grep"])
        reg = AgentRegistry(self.agents_dir())
        self.assertEqual(len(reg.errors), 1)
        self.assertIn("good-one", reg.names())

    def test_깨진_JSON_은_오류로_기록되고_넘어간다(self):
        (self.agents_dir() / "깨짐.json").write_text("{{{", encoding="utf-8")
        reg = AgentRegistry(self.agents_dir())
        self.assertTrue(any("깨짐" in e for e in reg.errors))
        self.assertIn("mini-puppy", reg.names())

    def test_없는_도구를_요구하면_만들_때_막는다(self):
        self.json_agent("ghost", tools=["존재하지_않는_도구"])
        reg = AgentRegistry(self.agents_dir())
        with self.assertRaises(KeyError):
            reg.build("ghost", scripted("x"), self.registry())

    def test_만들어진_에이전트가_허용_목록을_들고_있다(self):
        reg = AgentRegistry(None)
        agent = reg.build("reader", scripted("x"), self.registry())
        self.assertIsInstance(agent, Agent)
        self.assertEqual(agent.tools, reg.get("reader").tools)
        names = [s["name"] for s in self.registry().schemas(agent.tools)]
        self.assertNotIn("write_file", names)


class SubagentTest(TempCase):
    def build(self, max_depth=2):
        tools = self.registry()
        agents = AgentRegistry(None)
        self.답 = {"reader": scripted("읽어 봤다")}
        register_subagent_tool(tools, agents,
                               lambda spec: scripted("읽어 봤다"),
                               max_depth=max_depth)
        return tools, agents

    def test_서브에이전트_결과만_부모에게_돌아온다(self):
        tools, _agents = self.build()
        ws = self.workspace()
        out = tools.call("invoke_agent",
                         {"agent": "reader", "task": "a.py 를 읽어라"}, ctx=ws)
        self.assertTrue(out.ok)
        self.assertIn("[reader]", out.content)
        self.assertIn("읽어 봤다", out.content)
        self.assertIn("걸음", out.content)

    def test_깊이_한계를_넘으면_거절한다(self):
        tools, _agents = self.build(max_depth=1)
        ws = self.workspace()
        ws.depth = 1                     # 이미 한 겹 들어와 있다
        out = tools.call("invoke_agent", {"agent": "reader", "task": "또"},
                         ctx=ws)
        self.assertFalse(out.ok)
        self.assertIn("깊이 한계", out.content)

    def test_모르는_에이전트는_있는_것을_알려_준다(self):
        tools, _agents = self.build()
        out = tools.call("invoke_agent", {"agent": "없음", "task": "x"},
                         ctx=self.workspace())
        self.assertFalse(out.ok)
        self.assertIn("reader", out.content)
