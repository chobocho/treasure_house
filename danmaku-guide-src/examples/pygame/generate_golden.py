import argparse
import importlib.util
import json
from pathlib import Path


def generate(level):
    # region golden-guard
    src = Path(__file__).resolve().parent.parent.parent
    target = src / f'spec/golden/lv{level}.json'
    if target.exists():
        raise FileExistsError('기준 기록은 덮어쓸 수 없습니다')
    # endregion
    folder = Path(__file__).resolve().parent / f'lv{level}'
    spec = importlib.util.spec_from_file_location(f'golden_game_{level}', folder / 'game.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inputs = json.loads((folder / 'replay.json').read_text(encoding='utf-8'))
    seed = json.loads((src / 'spec/constants.json').read_text(encoding='utf-8'))['seed']
    stage_path = folder / 'stage.json'
    options = {'stage': json.loads(stage_path.read_text(encoding='utf-8'))} if stage_path.exists() else {}
    game = module.Game(seed, **options)
    cursor, bits, checkpoints = 0, 0, []
    for frame in range(1800):
        if cursor < len(inputs) and frame == inputs[cursor]['frame']:
            bits = inputs[cursor]['bits']
            cursor += 1
        game.step(bits)
        if game.frame in (60, 600, 1800):
            checkpoints.append(game.snapshot())
    # region golden-write
    with target.open('x', encoding='utf-8', newline='\n') as file:
        json.dump({'level': level, 'seed': seed, 'inputs': inputs, 'checkpoints': checkpoints}, file, ensure_ascii=False, indent=2)
        file.write('\n')
    print(f'Lv{level} 기준 기록을 실제 1800스텝 실행으로 생성했습니다')
    # endregion


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='새 pygame 단계의 기준 기록만 생성합니다')
    parser.add_argument('level', type=int, choices=range(1, 8))
    generate(parser.parse_args().level)
