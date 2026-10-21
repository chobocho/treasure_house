import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

from game import Game, LEFT, RIGHT, UP, DOWN, SHOOT, FOCUS, BOMB, START, PAUSE


# region scripted-input
def replay(game, events, frames):
    cursor, bits = 0, 0
    checkpoints = []
    for frame in range(frames):
        if cursor < len(events) and frame == events[cursor]['frame']:
            bits = events[cursor]['bits']
            cursor += 1
        game.step(bits)
        if game.frame in (60, 600, 1800):
            checkpoints.append(game.snapshot())
    return checkpoints
# endregion


# region keyboard
BINDINGS = ((LEFT, pygame.K_LEFT, pygame.K_a), (RIGHT, pygame.K_RIGHT, pygame.K_d),
            (UP, pygame.K_UP, pygame.K_w), (DOWN, pygame.K_DOWN, pygame.K_s),
            (SHOOT, pygame.K_z, pygame.K_SPACE), (FOCUS, pygame.K_LSHIFT, pygame.K_RSHIFT),
            (BOMB, pygame.K_x, pygame.K_x), (START, pygame.K_RETURN, pygame.K_RETURN),
            (PAUSE, pygame.K_p, pygame.K_p))


def read_input():
    keys = pygame.key.get_pressed()
    bits = 0
    for bit, first, second in BINDINGS:
        if keys[first] or keys[second]:
            bits |= bit
    return bits
# endregion


def interactive(game, frames):
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
    import pygame
    from render import Renderer
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((480, 640))
    pygame.display.set_caption('탄막 슈팅 · Lv1 이동과 발사')
    renderer = Renderer(screen)
    clock = pygame.time.Clock()
    accumulator, rendered, running = 0.0, 0, True
    # region interactive-loop
    while running and (frames == 0 or rendered < frames):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        if not running:
            break
        elapsed = 1 / 60 if os.environ.get('SDL_VIDEODRIVER') == 'dummy' else min(clock.tick(120) / 1000, .25)
        accumulator += elapsed
        bits = read_input()
        while accumulator + 1e-12 >= 1 / 60:
            game.step(bits)
            accumulator = max(0, accumulator - 1 / 60)
        renderer.draw(game, accumulator * 60)
        pygame.display.flip()
        rendered += 1
    # endregion
    pixels = pygame.image.tobytes(screen, 'RGB')
    not_blank = any(pixels[i] > 100 for i in range(0, len(pixels), 3))
    pygame.quit()
    return {'frames': rendered, 'notBlank': not_blank, 'state': game.snapshot()}


# region main-entry
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='방향키/WASD 이동, Z/Space 발사, Shift 집중 이동')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--frames', type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.frames <= 100000:
        parser.error('프레임 수는 0부터 100000까지입니다')
    game = Game()
    if args.headless:
        events = json.loads(Path(__file__).with_name('replay.json').read_text(encoding='utf-8'))
        result = {'checkpoints': replay(game, events, args.frames or 1800), 'state': game.snapshot()}
    else:
        result = interactive(game, args.frames)
    print(json.dumps(result, ensure_ascii=False))
# endregion
