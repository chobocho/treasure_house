"""셸 도구 — 4건."""
import sys

from mini_puppy.sh_tools import looks_dangerous, run_shell

from .helpers import TempCase


class ShTest(TempCase):
    def test_위험한_명령을_알아본다(self):
        self.assertTrue(looks_dangerous("sudo rm -rf / --no-preserve-root"))
        self.assertTrue(looks_dangerous("  DD IF=/dev/zero of=/dev/sda"))
        self.assertFalse(looks_dangerous("git status"))

    def test_막힌_명령은_실행_전에_거부된다(self):
        reg = self.registry()
        out = reg.call("run_command", {"command": "rm -rf /"},
                       ctx=self.workspace())
        self.assertFalse(out.ok)
        self.assertIn("막힌 명령", out.content)

    def test_종료코드와_출력이_돌아온다(self):
        reg = self.registry()
        code = "import sys; print('나왔다'); sys.exit(3)"
        out = reg.call("run_command",
                       {"command": '"%s" -c "%s"' % (sys.executable, code)},
                       ctx=self.workspace())
        self.assertTrue(out.ok)
        self.assertIn("종료코드 3", out.content)
        self.assertIn("나왔다", out.content)

    def test_시간_제한이_지나면_죽인다(self):
        res = run_shell('"%s" -c "import time; time.sleep(30)"' % sys.executable,
                        cwd=str(self.tmp), timeout=2)
        self.assertTrue(res["timed_out"])
        self.assertLess(res["seconds"], 15)
