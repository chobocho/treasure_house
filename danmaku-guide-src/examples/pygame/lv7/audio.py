from array import array
from math import sin, pi
import pygame

# region tone
# 합성은 로딩 때만 수행하며 게임 갱신의 난수를 소비하지 않는다. 시간·공간 O(샘플 수).
def tone(frequency, duration, rate=22050):
    count = int(duration * rate)
    result = array('h', [0]) * count
    for i in range(count):
        envelope = min(1.0, i / 110) * (1 - i / max(1, count))
        result[i] = int(sin(2 * pi * frequency * i / rate) * envelope * 4500)
    return result
# endregion


class Audio:
    # region audio-init
    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.sounds = [pygame.mixer.Sound(buffer=tone(f, .08).tobytes())
                           for f in (660, 130, 220, 880, 90, 990, 440, 110)]
            self.music = pygame.mixer.Sound(buffer=self.melody().tobytes())
            self.music.play(loops=-1)
            self.enabled = True
        except pygame.error:
            self.sounds = []
    # endregion

    # region melody
    def melody(self):
        samples = array('h')
        for frequency in (220, 330, 440, 330, 262, 392, 523, 392):
            samples.extend(tone(frequency, .4))
        return samples
    # endregion

    # region audio-consume
    def consume(self, game):
        if not self.enabled:
            return
        played = 0
        for i in range(game.event_count):
            kind = game.event_kind[i]
            mask = 1 << kind
            if not played & mask:
                self.sounds[kind - 1].play()
                played |= mask
        if game.paused or game.status != 1:
            self.music.set_volume(.08)
        else:
            self.music.set_volume(.2)
    # endregion

    # region audio-close
    def close(self):
        if self.enabled:
            pygame.mixer.stop()
            pygame.mixer.quit()
            self.enabled = False
    # endregion
