# -*- coding: utf-8 -*-
"""우리 쇼 파일(JSON)을 Blender 장면으로 — 드론마다 구 하나,
키프레임마다 위치·색 키 (12부).

**이 기계에서는 Blender 로 실행하지 않았다** — 설치할 수 없다(PLAN.md
§9 결정 10). 쓰는 bpy 호출은 전부 받아 둔 Blender API 문서로 확인했고,
시험은 호출을 기록하는 가짜 bpy 위에서 이 파일의 논리만 돌린다.

    blender --background --python ex/blender_import_show.py -- show.json

키프레임 사이를 Blender 가 어떻게 잇는지는 이 예제가 정하지 않는다 —
우리 쇼의 β(u)와 같다는 보장이 없다. 모양까지 맞추려면 fps 마다 한
줄인 CSV(ex/skybrush_csv.py, droneshow csv)를 읽어 키를 넣는다.
"""
import json
import sys

import bpy  # Blender 안에서만 있다


def main(path):
    show = json.load(open(path, encoding='utf-8'))
    fps = show['fps']
    for d in show['drones']:
        first = d['keyframes'][0]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15,
                                             location=first[1:4])
        obj = bpy.context.active_object
        obj.name = 'drone_%03d' % d['id']
        for k in d['keyframes']:
            # Blender 의 첫 프레임은 1
            f = round(k[0] * fps) + 1
            obj.location = k[1:4]
            obj.keyframe_insert(data_path='location', frame=f)
            obj.color = [c / 255 for c in k[4:7]] + [1.0]
            obj.keyframe_insert(data_path='color', frame=f)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1])
