import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile


def tools():
    path = Path(__file__).parent / 'tools.py'
    if not path.exists():
        raise AssertionError('실행 가능한 배포·진단 도구가 있어야 합니다')
    spec = importlib.util.spec_from_file_location('pygame_tools', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ToolTests(unittest.TestCase):
    def test_zip_contains_complete_source_without_user_data_and_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'game.zip'
            tools().package(archive)
            with zipfile.ZipFile(archive) as source:
                names = source.namelist()
                for required in ['main.py', 'game.py', 'render.py', 'audio.py', 'storage.py', 'stage.json', 'replay.json', 'LICENSE-NOTO.txt', 'requirements.txt']:
                    self.assertIn(required, names)
                self.assertFalse(any('best.json' in n or '__pycache__' in n for n in names))
                source.extractall(Path(directory) / 'unpacked')
            result = subprocess.run([sys.executable, str(Path(directory)/'unpacked/main.py'), '--frames', '2'], cwd=directory, capture_output=True, text=True, check=True)
            self.assertTrue(json.loads(result.stdout)['notBlank'])

    def test_profile_reports_real_steps_and_environment(self):
        report = tools().profile(60)
        self.assertEqual(report['steps'], 60)
        self.assertEqual(report['state']['frame'], 60)
        self.assertGreater(report['elapsedMs'], 0)
        self.assertGreater(report['calls'], 0)
        self.assertIn('python', report)
        self.assertIn('top', report)
        self.assertEqual(len(report['top']), 8)

    def test_profile_rejects_invalid_limits(self):
        for value in [0, -1, 1.5, True, 100001]:
            with self.assertRaises(ValueError):
                tools().profile(value)
