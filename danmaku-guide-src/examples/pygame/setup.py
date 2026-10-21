# region imports
import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame
# endregion


def probe(frames):
    # region window
    pygame.display.init()
    screen = pygame.display.set_mode((480, 640))
    pygame.display.set_caption('탄막 슈팅 · 환경 확인')
    # endregion
    # region image
    asset = Path(__file__).resolve().parent.parent / 'assets/noto-emoji/rocket.png'
    image = pygame.image.load(asset).convert_alpha()
    image = pygame.transform.smoothscale(image, (64, 64))
    # endregion
    # region probe-loop
    drawn = 0
    running = True
    clock = pygame.time.Clock()
    while running and drawn < frames:
        # region setup-events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if not running:
            break
        # endregion
        # region setup-draw
        screen.fill((8, 21, 35))
        screen.blit(image, (208, 488))
        pygame.display.flip()
        # endregion
        drawn += 1
        if os.environ.get('SDL_VIDEODRIVER') != 'dummy':
            clock.tick(60)
    # endregion
    # region probe-result
    pixels = pygame.image.tobytes(screen, 'RGB')
    blank = bytes((8, 21, 35)) * (480 * 640)
    result = {'pygame': pygame.version.ver, 'screen': list(screen.get_size()),
              'sprite': list(image.get_size()), 'frames': drawn,
              'notBlank': hashlib.sha256(pixels).digest() != hashlib.sha256(blank).digest()}
    pygame.quit()
    return result
    # endregion


# region frame-limit
def frame_limit(value):
    try:
        frames = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('프레임 수는 정수여야 합니다') from error
    if not 1 <= frames <= 10000:
        raise argparse.ArgumentTypeError('프레임 수는 1부터 10000까지입니다')
    return frames
# endregion


# region setup-main
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pygame 창과 이미지 로딩을 확인합니다')
    parser.add_argument('--frames', type=frame_limit, default=60)
    args = parser.parse_args()
    print(json.dumps(probe(args.frames), ensure_ascii=False))
# endregion
