import argparse
import cProfile
import importlib.util
import json
from pathlib import Path
import platform
import pstats
import time
import zipfile

HERE = Path(__file__).resolve().parent

# region package
def package(target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    names = ['main.py', 'game.py', 'render.py', 'audio.py', 'storage.py',
             'stage.json', 'replay.json', 'LICENSE-NOTO.txt']
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(HERE / 'lv7' / name, name)
        archive.write(HERE / 'requirements.txt', 'requirements.txt')
    return {'archive': target.name, 'files': names + ['requirements.txt'], 'bytes': target.stat().st_size}
# endregion


# region profile-load
def profile(frames=1800):
    if type(frames) is not int or not 1 <= frames <= 100000:
        raise ValueError('측정 스텝은 1부터 100000까지 정수입니다')
    path = HERE / 'lv7/game.py'
    spec = importlib.util.spec_from_file_location('profile_game', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    game = module.Game(stage=json.loads((HERE / 'lv7/stage.json').read_text(encoding='utf-8')))
    inputs = json.loads((HERE / 'lv7/replay.json').read_text(encoding='utf-8'))
    cursor, bits = 0, 0
    profiler = cProfile.Profile()
    # endregion
    # region profile-run
    start = time.perf_counter()
    profiler.enable()
    for frame in range(frames):
        if cursor < len(inputs) and frame == inputs[cursor]['frame']:
            bits = inputs[cursor]['bits']
            cursor += 1
        game.step(bits)
    profiler.disable()
    elapsed = (time.perf_counter() - start) * 1000
    # endregion
    # region profile-report
    stats = pstats.Stats(profiler)
    ordered = sorted(stats.stats.items(), key=lambda row: row[1][3], reverse=True)[:8]
    top = [{'function': key[2], 'calls': value[1], 'cumulativeMs': round(value[3] * 1000, 3)}
           for key, value in ordered]
    return {'python': platform.python_version(), 'machine': platform.machine(),
            'steps': frames, 'elapsedMs': round(elapsed, 3), 'calls': stats.total_calls,
            'state': game.snapshot(), 'activeSteps': game.time,
            'method': 'cProfile이 켜진 Lv7 자동 재생; 렌더·오디오·파일 읽기 제외',
            'top': top}
    # endregion


# region tool-entry
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pygame 소스 배포와 실제 자동 재생 프로파일')
    parser.add_argument('action', choices=['package', 'profile', 'diagnose'])
    args = parser.parse_args()
    if args.action == 'package':
        result = package(HERE.parent.parent / 'dist/pygame-lv7.zip')
    elif args.action == 'profile':
        result = profile()
    else:
        import pygame
        result = {'python': platform.python_version(), 'pygame': pygame.version.ver,
                  'machine': platform.machine(), 'screen': [480, 640]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
# endregion
