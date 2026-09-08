"""메시지 버스 — 6건."""
import unittest

from mini_puppy.bus import KINDS, CollectingSink, Message, MessageBus


class BusTest(unittest.TestCase):
    def test_모르는_종류는_거부한다(self):
        with self.assertRaises(ValueError):
            Message(kind="노래", text="x")

    def test_모든_종류가_통과한다(self):
        for kind in KINDS:
            self.assertEqual(Message(kind, "t").kind, kind)

    def test_싱크가_순서대로_받는다(self):
        bus = MessageBus()
        sink = CollectingSink()
        bus.subscribe(sink)
        bus.info("하나")
        bus.warn("둘")
        bus.error("셋")
        self.assertEqual([m.text for m in sink.messages], ["하나", "둘", "셋"])
        self.assertEqual([m.kind for m in sink.messages],
                         ["info", "warn", "error"])

    def test_싱크가_죽어도_다음_싱크는_받는다(self):
        bus = MessageBus()
        good = CollectingSink()

        def bad(_msg):
            raise RuntimeError("렌더러 사고")

        bus.subscribe(bad)
        bus.subscribe(good)
        bus.emit("info", "살아남아라")
        self.assertEqual(len(good), 1)
        self.assertEqual(len(bus.sink_errors), 1)

    def test_구독을_끊으면_안_받는다(self):
        bus = MessageBus()
        sink = CollectingSink()
        bus.subscribe(sink)
        bus.info("전")
        bus.unsubscribe(sink)
        bus.info("후")
        self.assertEqual(len(sink), 1)
        self.assertEqual(len(bus.log), 2)      # 버스 자체 기록은 남는다

    def test_종류로_거르는_싱크(self):
        bus = MessageBus()
        only_tools = CollectingSink(kinds=["tool", "tool_out"])
        bus.subscribe(only_tools)
        bus.emit("tool", "read_file")
        bus.emit("agent", "다 됐다")
        bus.emit("tool_out", "내용")
        self.assertEqual(len(only_tools), 2)


if __name__ == "__main__":
    unittest.main()
