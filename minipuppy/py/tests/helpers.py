"""시험이 함께 쓰는 도구."""
import shutil
import tempfile
import unittest
from pathlib import Path

from mini_puppy.bus import CollectingSink, MessageBus
from mini_puppy.config import Config
from mini_puppy.fs_tools import Workspace
from mini_puppy.model import ModelReply, ScriptedModel, ToolCall
from mini_puppy.tools import ToolRegistry
from mini_puppy import fs_tools, sh_tools


class TempCase(unittest.TestCase):
    """임시 디렉터리를 뿌리로 잡고 끝나면 지운다."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="minipuppy-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, rel, text):
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def registry(self, timeout=10):
        reg = ToolRegistry()
        fs_tools.register(reg)
        sh_tools.register(reg, default_timeout=timeout)
        return reg

    def workspace(self, yolo=True, approver=None):
        ws = Workspace(self.tmp, yolo=yolo, approver=approver)
        ws.depth = 0
        return ws

    def bus(self):
        bus = MessageBus()
        sink = CollectingSink()
        bus.subscribe(sink)
        return bus, sink

    def config(self, **over):
        cfg = Config(self.tmp / "cfg", environ={})
        for k, v in over.items():
            cfg.set(k, v)
        return cfg


def call(name, **args):
    """도구 호출 한 건을 만든다."""
    return ToolCall(id="c-" + name, name=name, args=args)


def reply(text="", *calls):
    return ModelReply(text=text, tool_calls=list(calls))


def scripted(*replies):
    return ScriptedModel("scripted", list(replies))
