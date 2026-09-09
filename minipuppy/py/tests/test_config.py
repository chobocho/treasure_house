"""설정 세 겹 — 8건."""
from mini_puppy.config import DEFAULTS, Config

from .helpers import TempCase


class ConfigTest(TempCase):
    def cfg(self, environ=None):
        return Config(self.tmp / "cfg", environ=environ or {})

    def test_기본값이_깔린다(self):
        c = self.cfg()
        self.assertEqual(c.get("model"), DEFAULTS["model"])
        self.assertEqual(c.source("model"), "default")

    def test_파일이_기본값을_덮는다(self):
        c = self.cfg()
        c.set("model", "gpt-4.1")
        self.assertEqual(c.get("model"), "gpt-4.1")
        self.assertEqual(c.source("model"), "file")

    def test_환경변수가_파일을_덮는다(self):
        c = self.cfg(environ={"MINI_PUPPY_MODEL": "sonnet"})
        c.set("model", "gpt-4.1")
        self.assertEqual(c.get("model"), "sonnet")
        self.assertEqual(c.source("model"), "env")

    def test_환경변수가_덮는_키를_set_해도_get_은_안_바뀐다(self):
        c = self.cfg(environ={"MINI_PUPPY_MODEL": "sonnet"})
        c.set("model", "haiku")
        self.assertEqual(c.get("model"), "sonnet")
        # 파일에는 확실히 들어갔다
        self.assertIn("haiku", (self.tmp / "cfg" / "puppy.cfg").read_text("utf-8"))

    def test_형_변환(self):
        c = self.cfg()
        c.set("yolo_mode", "yes")
        c.set("context_window", "32000")
        c.set("compaction_threshold", "0.6")
        self.assertIs(c.get_bool("yolo_mode"), True)
        self.assertEqual(c.get_int("context_window"), 32000)
        self.assertAlmostEqual(c.get_float("compaction_threshold"), 0.6)

    def test_파일이_바뀌면_캐시가_풀린다(self):
        c = self.cfg()
        c.set("agent", "reader")
        self.assertEqual(c.get("agent"), "reader")
        path = self.tmp / "cfg" / "puppy.cfg"
        path.write_text("[puppy]\nagent = tester\n", encoding="utf-8")
        self.assertEqual(c.get("agent"), "tester")

    def test_깨진_설정_파일은_기본값으로_돌아간다(self):
        path = self.tmp / "cfg" / "puppy.cfg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("이건 INI 가 아니다 ]]] [[[", encoding="utf-8")
        c = self.cfg()
        self.assertEqual(c.get("model"), DEFAULTS["model"])

    def test_unset_하면_아래층이_다시_보인다(self):
        c = self.cfg()
        c.set("model", "gpt-4.1")
        c.unset("model")
        self.assertEqual(c.get("model"), DEFAULTS["model"])
        self.assertEqual(c.source("model"), "default")
