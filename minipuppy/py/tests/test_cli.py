"""명령줄 껍데기 — 7건."""
import json

from mini_puppy.bus import CollectingSink, MessageBus
from mini_puppy.cli import COMMANDS, Shell, build_parser

from .helpers import TempCase


class CliTest(TempCase):
    def shell(self, **cfg):
        (self.tmp / "work").mkdir(exist_ok=True)
        config = self.config(yolo_mode="true", **cfg)
        (config.dir / "models.json").write_text(json.dumps({
            "scripted": {"type": "scripted",
                         "replies": ["대본이 답한다"]},
            "교대": {"type": "round_robin", "models": ["scripted"],
                     "rotate_every": 2},
        }, ensure_ascii=False), encoding="utf-8")
        bus = MessageBus()
        sink = CollectingSink()
        bus.subscribe(sink)
        return Shell(str(self.tmp / "work"), config, bus), sink

    def test_명령이_전부_등록돼_있다(self):
        for name in ("help", "agent", "model", "tools", "compact", "config",
                     "session", "sh", "quit"):
            self.assertIn(name, COMMANDS)

    def test_한_턴이_돌고_세션이_저장된다(self):
        sh, sink = self.shell()
        sh.turn("안녕")
        self.assertEqual(sink.messages[-1].text, "대본이 답한다")
        saved = sh.store.load(sh.session.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.title, "안녕")
        self.assertGreaterEqual(len(saved.messages), 3)

    def test_에이전트를_바꾸면_기록이_새로_시작한다(self):
        sh, sink = self.shell()
        sh.turn("첫 마디")
        self.assertGreater(len(sh.history), 1)
        sh.turn("/agent reader")
        self.assertIsNone(sh.history)
        self.assertEqual(sh.agent_name, "reader")

    def test_tools_명령이_막힌_도구를_알려_준다(self):
        sh, sink = self.shell()
        sh.turn("/agent reader")
        sh.turn("/tools")
        out = sink.messages[-1].text
        self.assertIn("read_file", out)
        self.assertIn("막힌 도구", out)
        self.assertIn("write_file", out.split("막힌 도구")[1])

    def test_config_명령이_층을_보여_준다(self):
        sh, sink = self.shell()
        sh.turn("/config model=교대")
        self.assertIn("file", sink.messages[-1].text)
        self.assertEqual(sh.config.get("model"), "교대")

    def test_모르는_명령은_안내로_끝난다(self):
        sh, sink = self.shell()
        sh.turn("/없는명령")
        self.assertEqual(sink.messages[-1].kind, "warn")
        self.assertIn("/help", sink.messages[-1].text)


class ParserTest(TempCase):
    def test_한_번_모드_인자를_읽는다(self):
        args = build_parser().parse_args(["-p", "고쳐줘", "-C", "/tmp",
                                          "--yolo"])
        self.assertEqual(args.prompt, "고쳐줘")
        self.assertTrue(args.yolo)
