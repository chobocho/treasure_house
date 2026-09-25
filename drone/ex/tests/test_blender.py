# -*- coding: utf-8 -*-
"""blender 예제 시험 — Blender 없이, 호출을 기록하는 가짜 bpy 로.

증명하는 것은 둘뿐이다: 파일이 문법적으로 맞고(py_compile), 드론마다
구를 하나 만들어 키프레임마다 위치·색 키를 넣는다. Blender 가 그 키를
어떻게 보간하는지는 여기서 모른다(12부 캡션이 그렇게 적는다).
"""
import json
import os
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.dirname(HERE)


class FakeObj:
    def __init__(self, log):
        self.log, self.name = log, ''
        self.location = self.color = None

    def keyframe_insert(self, data_path, frame):
        self.log.append((self.name, data_path, frame,
                         list(getattr(self, data_path))))


def fake_bpy(log):
    bpy = types.ModuleType('bpy')
    ctx = types.SimpleNamespace(active_object=None)

    def add(radius, location):
        ctx.active_object = FakeObj(log)
        log.append(('sphere', radius, list(location)))
    bpy.ops = types.SimpleNamespace(mesh=types.SimpleNamespace(
        primitive_uv_sphere_add=add))
    bpy.context = ctx
    return bpy


class Blender(unittest.TestCase):
    def test_compiles(self):
        p = os.path.join(EX, 'blender_import_show.py')
        compile(open(p, encoding='utf-8').read(), p, 'exec')

    def test_keys_per_keyframe(self):
        log = []
        sys.modules['bpy'] = fake_bpy(log)
        sys.path.insert(0, EX)
        try:
            import blender_import_show as B
            kf = [[0.0, 1, 2, 3, 255, 0, 0],
                  [2.0, 4, 5, 6, 0, 0, 255, 'T']]
            show = {'fps': 25, 'drones': [{'id': 3, 'keyframes': kf}]}
            p = os.path.join(tempfile.mkdtemp(), 's.json')
            json.dump(show, open(p, 'w'))
            B.main(p)
        finally:
            del sys.modules['bpy']
        self.assertEqual(log[0], ('sphere', 0.15, [1, 2, 3]))
        self.assertIn(('drone_003', 'location', 51, [4, 5, 6]), log)
        red = [1.0, 0.0, 0.0, 1.0]
        self.assertIn(('drone_003', 'color', 1, red), log)
        self.assertEqual(len(log), 1 + 2 * 2)


if __name__ == '__main__':
    unittest.main()
