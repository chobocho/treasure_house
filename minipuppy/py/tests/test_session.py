"""세션 저장과 이주 — 8건."""
import json
import os

from mini_puppy.session import (SCHEMA_VERSION, Session, SessionStore,
                                atomic_write_json, atomic_write_text,
                                migrate, read_json)

from .helpers import TempCase


class SessionTest(TempCase):
    def store(self):
        return SessionStore(self.tmp / "sessions")

    def test_원자적_쓰기가_임시파일을_안_남긴다(self):
        target = self.tmp / "out" / "a.txt"
        atomic_write_text(target, "내용")
        self.assertEqual(target.read_text("utf-8"), "내용")
        leftovers = [p for p in target.parent.iterdir() if p.suffix == ".tmp"]
        self.assertEqual(leftovers, [])

    def test_덮어써도_이전_내용은_사라진다(self):
        target = self.tmp / "a.txt"
        atomic_write_text(target, "옛것")
        atomic_write_text(target, "새것")
        self.assertEqual(target.read_text("utf-8"), "새것")

    def test_쓰다_실패하면_원본이_남는다(self):
        target = self.tmp / "a.json"
        atomic_write_json(target, {"살아있음": True})
        before = target.read_text("utf-8")

        class Boom:
            def __repr__(self):
                raise RuntimeError("직렬화 실패")

        with self.assertRaises(Exception):
            atomic_write_json(target, {"x": Boom()})
        self.assertEqual(target.read_text("utf-8"), before)
        self.assertEqual([p for p in self.tmp.iterdir() if p.suffix == ".tmp"], [])

    def test_깨진_JSON_은_default_를_준다(self):
        path = self.tmp / "broken.json"
        path.write_text("{{{", encoding="utf-8")
        self.assertEqual(read_json(path, default={"기본": 1}), {"기본": 1})

    def test_저장하고_다시_읽는다(self):
        st = self.store()
        s = Session(agent="reader", title="첫 세션")
        s.messages = [{"role": "user", "content": "안녕"}]
        st.save(s)
        got = st.load(s.id)
        self.assertEqual(got.agent, "reader")
        self.assertEqual(got.messages[0]["content"], "안녕")
        self.assertEqual(got.version, SCHEMA_VERSION)

    def test_v1_세션이_v2_로_올라간다(self):
        raw = {"version": 1, "id": "old1", "messages": ["옛날 메시지"]}
        got = Session.from_dict(raw)
        self.assertEqual(got.version, 2)
        self.assertEqual(got.messages, [{"role": "user", "content": "옛날 메시지"}])
        self.assertEqual(got.agent, "mini-puppy")

    def test_목록은_최신순이고_깨진_파일은_건너뛴다(self):
        st = self.store()
        st.dir.mkdir(parents=True, exist_ok=True)
        (st.dir / "쓰레기.json").write_text("아님", encoding="utf-8")
        a = Session(title="먼저")
        st.save(a)
        b = Session(title="나중")
        b.updated = a.updated + 100
        st.save(b)
        b.updated = a.updated + 100
        atomic_write_json(st.path_for(b.id), b.to_dict())
        titles = [s.title for s in st.list()]
        self.assertEqual(titles[0], "나중")
        self.assertEqual(len(titles), 2)

    def test_지우기(self):
        st = self.store()
        s = Session()
        st.save(s)
        self.assertTrue(st.delete(s.id))
        self.assertFalse(st.delete(s.id))
        self.assertIsNone(st.load(s.id))
