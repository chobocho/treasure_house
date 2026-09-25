# -*- coding: utf-8 -*-
"""golden 시험 — golden/*.json 이 지금 파이썬 판이 내는 값과 같다.

파이썬 판을 고쳐 값이 바뀌었는데 골든을 다시 쓰지 않으면, 자바스크립트
판은 옛 값에 맞춰 초록이 된다. 그 틈을 여기서 막는다."""
import unittest

import tests.write_golden as W


class Golden(unittest.TestCase):
    def test_files_are_current(self):
        for name in W.GOLDEN:
            with self.subTest(name=name):
                with open('%s/%s.json' % (W.OUT, name),
                          encoding='utf-8') as f:
                    self.assertEqual(f.read(), W.text_of(name))


if __name__ == '__main__':
    unittest.main()
