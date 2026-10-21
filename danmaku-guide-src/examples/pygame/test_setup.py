import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import importlib.metadata

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent


class SetupTests(unittest.TestCase):
    def test_distribution_version_is_pinned(self):
        requirement = (HERE / 'requirements.txt').read_text(encoding='utf-8').strip()
        name, version = requirement.split('==')
        self.assertEqual(importlib.metadata.version(name), version)

    def test_all_image_assets_load(self):
        import pygame
        for name in ['rocket.png', 'alien.png', 'bullet.png']:
            image = pygame.image.load(str(SRC / 'examples/assets/noto-emoji' / name))
            self.assertEqual(image.get_size(), (128, 128))

    def test_setup_draws_and_loads_sprite(self):
        script = HERE / 'setup.py'
        self.assertTrue(script.exists(), '실행할 초기화 예제가 있어야 한다')
        result = subprocess.run([sys.executable, str(script), '--frames', '2'], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        self.assertEqual(data['screen'], [480, 640])
        self.assertEqual(data['frames'], 2)
        self.assertEqual(data['sprite'], [64, 64])
        self.assertTrue(data['notBlank'])

    def test_invalid_frame_limits_fail(self):
        script = HERE / 'setup.py'
        self.assertTrue(script.exists())
        for frames in ['0', '-1', '10001', 'not-a-number']:
            result = subprocess.run([sys.executable, str(script), '--frames', frames], capture_output=True)
            self.assertEqual(result.returncode, 2)

    def test_commands_and_capture(self):
        script = HERE / 'commands.sh'
        self.assertTrue(script.exists(), '슬라이드 명령은 실제 실행 파일이어야 한다')
        result = subprocess.run(['bash', str(script), 'setup', '--frames', '1'], cwd=SRC, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['frames'], 1)


if __name__ == '__main__':
    unittest.main()
