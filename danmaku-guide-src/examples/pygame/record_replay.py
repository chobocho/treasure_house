"""Lv7 기준 기록 입력을 자동 조종으로 다시 만든다.

사람이 손으로 녹화한 입력은 패턴이 바뀌면 곧바로 게임 오버가 되어 기준 기록이 보스 후반을
검증하지 못한다. 그래서 실제 게임 복사본으로 몇 스텝 앞을 내다보는 결정적 조종기로 입력을 만든다.
같은 게임 규칙이면 언제 다시 돌려도 같은 입력이 나온다.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent
HORIZON, DECIDE_EVERY, FRAMES = 20, 2, 1800


def load(level):
    spec = importlib.util.spec_from_file_location(f'replay_game_{level}', HERE / f'lv{level}' / 'game.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidates(m):
    moves = [0, m.LEFT, m.RIGHT, m.UP, m.DOWN, m.LEFT | m.UP, m.LEFT | m.DOWN, m.RIGHT | m.UP, m.RIGHT | m.DOWN]
    # 집중 이동은 좁은 틈을 지날 때만 쓸모가 있으므로 정지 이외의 여덟 방향에만 붙인다.
    return moves + [move | m.FOCUS for move in moves[1:]]


def nearest(game):
    pool, best = game.bullets, 1e9
    for i in range(pool.count):
        if pool.kind[i] == 1:
            dx, dy = pool.x[i] - game.player_x, pool.y[i] - game.player_y
            best = min(best, dx * dx + dy * dy)
    return best ** .5


def wants_shot(game):
    # 마지막 체크포인트에서 보스 3단계를 보이도록 3단계에서는 보스 체력을 40 아래로 깎지 않는다.
    boss = game.find_boss()
    return not (game.phase == 3 and boss >= 0 and game.enemies.hp[boss] <= 40)


# region replay-evaluate
# 후보 하나를 HORIZON 스텝 유지했을 때의 점수. 시간 O(H·(b+e)), 추가 공간은 게임 복사본 하나.
def evaluate(game, bits):
    trial = copy.deepcopy(game)
    lives, closest = trial.lives, 1e9
    for _ in range(HORIZON):
        trial.step(bits)
        if trial.lives < lives:
            return -1e6 + closest
        closest = min(closest, nearest(trial))
    # 적탄과의 거리를 가장 크게 보되, 화면 아래 가운데에 머무르려는 약한 선호를 더해 벽에 몰리지 않게 한다.
    home = abs(trial.player_x - 240) / 240 + abs(trial.player_y - 540) / 640
    return min(closest, 60) - 4 * home
# endregion


def record(level=7):
    m = load(level)
    stage = json.loads((HERE / f'lv{level}' / 'stage.json').read_text(encoding='utf-8'))
    seed = json.loads((SRC / 'spec/constants.json').read_text(encoding='utf-8'))['seed']
    game = m.Game(seed, stage=stage)
    inputs, bits = [], None
    for frame in range(FRAMES):
        if frame % DECIDE_EVERY == 0:
            shot = m.SHOOT if wants_shot(game) else 0
            scored = [(evaluate(game, move | shot), -index, move | shot) for index, move in enumerate(candidates(m))]
            best = max(scored)
            choice = best[2]
            # 어느 후보도 피격을 피하지 못하면 폭탄으로 적탄을 지운다.
            if best[0] < -1e5 and game.bombs > 0:
                choice |= m.BOMB
        if choice != bits:
            inputs.append({'frame': frame, 'bits': choice})
            bits = choice
        game.step(bits)
        if choice & m.BOMB:
            choice &= ~m.BOMB
    return inputs, game


def main():
    parser = argparse.ArgumentParser(description='Lv7 기준 기록 입력을 결정적 자동 조종으로 만든다')
    parser.add_argument('--write', action='store_true', help='세 트랙의 lv7/replay.json을 덮어쓴다')
    args = parser.parse_args()
    inputs, game = record()
    print(f'입력 변화 {len(inputs)}개, 1800스텝 뒤 목숨 {game.lives}, 단계 {game.phase}, 폭탄 {game.bombs}, 점수 {game.score}')
    if args.write:
        text = '[\n' + ',\n'.join(f'  {{"frame": {i["frame"]}, "bits": {i["bits"]}}}' for i in inputs) + '\n]\n'
        for track in ('pygame', 'canvas-ts', 'three-ts'):
            (SRC / 'examples' / track / 'lv7' / 'replay.json').write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
