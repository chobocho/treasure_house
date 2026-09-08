"""파일 도구 — 9건. 가드레일이 진짜 막는지 확인한다."""
from .helpers import TempCase


class FsTest(TempCase):
    def setUp(self):
        super().setUp()
        self.reg = self.registry()
        self.write("src/a.py", "def hi():\n    return '안녕'\n")
        self.write("src/b.py", "x = 1\ny = 2\n")
        self.write("node_modules/junk.py", "무시되어야 한다\n")

    def t(self, name, ws=None, **args):
        return self.reg.call(name, args, ctx=ws or self.workspace())

    # ---- 가드레일 ------------------------------------------------------
    def test_상위_경로로_못_빠져나간다(self):
        for 나쁜 in ("../secret", "../../etc/passwd", "src/../../밖"):
            out = self.t("read_file", path=나쁜)
            self.assertFalse(out.ok, 나쁜)
            self.assertIn("뿌리 밖", out.content)

    def test_절대경로도_뿌리_밖이면_막힌다(self):
        out = self.t("read_file", path=str(self.tmp.parent / "밖.txt"))
        self.assertFalse(out.ok)

    def test_yolo_가_아니면_승인_창구를_거친다(self):
        본_것 = []

        def 거절(action, rel):
            본_것.append((action, rel))
            return False

        ws = self.workspace(yolo=False, approver=거절)
        out = self.t("write_file", ws=ws, path="새파일.txt", content="x")
        self.assertFalse(out.ok)
        self.assertIn("거절", out.content)
        self.assertEqual(len(본_것), 1)
        self.assertFalse((self.tmp / "새파일.txt").exists())

    def test_승인하면_써진다(self):
        ws = self.workspace(yolo=False, approver=lambda a, r: True)
        out = self.t("write_file", ws=ws, path="새파일.txt", content="내용")
        self.assertTrue(out.ok)
        self.assertEqual((self.tmp / "새파일.txt").read_text("utf-8"), "내용")
        self.assertIn("새파일.txt", ws.writes[0])

    # ---- 읽기 ----------------------------------------------------------
    def test_행_번호를_붙여_읽는다(self):
        out = self.t("read_file", path="src/a.py")
        self.assertTrue(out.ok)
        self.assertTrue(out.content.startswith("1  def hi():"))

    def test_행_범위로_자른다(self):
        out = self.t("read_file", path="src/b.py", start=2, end=2)
        self.assertEqual(out.content.strip(), "2  y = 2")

    def test_목록이_잡동사니_디렉터리를_건너뛴다(self):
        out = self.t("list_files", pattern="*.py")
        self.assertIn("src/a.py", out.content)
        self.assertNotIn("node_modules", out.content)

    # ---- 고치기 --------------------------------------------------------
    def test_여러_군데_걸리면_거절한다(self):
        self.write("dup.py", "x = 1\nx = 1\n")
        out = self.t("edit_file", path="dup.py", find="x = 1", replace="x = 2")
        self.assertFalse(out.ok)
        self.assertIn("2군데", out.content)
        self.assertEqual((self.tmp / "dup.py").read_text("utf-8"), "x = 1\nx = 1\n")

    def test_없는_문자열은_힌트를_준다(self):
        out = self.t("edit_file", path="src/a.py", find="없는것",
                       replace="x")
        self.assertFalse(out.ok)
        self.assertIn("공백", out.content)
