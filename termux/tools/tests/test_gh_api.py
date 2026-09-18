# -*- coding: utf-8 -*-
"""gh_api.py 시험 — GitHub API 응답을 캐시에서 읽는 일.

비인증 API 는 시간당 60번이다. 그래서 응답은 전부 sources/gh/ 에
남기고 다시 묻지 않는다. 시험은 캐시만 쓴다 — 네트워크에 닿으면
offline=True 가 LookupError 로 막는다.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import gh_api                                      # noqa: E402

REL = [
    {'tag_name': 'v0.2', 'name': 'v0.2', 'draft': False,
     'prerelease': False, 'published_at': '2021-03-04T05:06:07Z',
     'html_url': 'https://github.com/o/r/releases/tag/v0.2'},
    {'tag_name': 'v0.1-beta', 'name': '', 'draft': False,
     'prerelease': True, 'published_at': '2020-01-02T00:00:00Z',
     'html_url': 'https://github.com/o/r/releases/tag/v0.1-beta'},
]


class GhTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def seed(self, path, obj):
        p = os.path.join(self.d, gh_api.cache_name(path))
        io.open(p, 'w', encoding='utf-8').write(json.dumps(obj))

    def test_cache_name_is_flat_and_stable(self):
        n = gh_api.cache_name('repos/o/r/releases?per_page=100&page=1')
        self.assertEqual(
            n, 'repos_o_r_releases_per_page_100_page_1.json')

    def test_get_reads_cache_without_network(self):
        self.seed('repos/o/r', {'x': 1})
        self.assertEqual(gh_api.get('repos/o/r', self.d, offline=True),
                         {'x': 1})

    def test_offline_miss_raises(self):
        with self.assertRaises(LookupError):
            gh_api.get('repos/o/none', self.d, offline=True)

    def test_releases_sorted_oldest_first(self):
        self.seed('repos/o/r/releases?per_page=100&page=1', REL)
        rows = gh_api.releases('o/r', self.d, offline=True)
        self.assertEqual([r['tag'] for r in rows],
                         ['v0.1-beta', 'v0.2'])
        self.assertEqual(rows[1]['date'], '2021-03-04')
        self.assertTrue(rows[0]['prerelease'])
        self.assertEqual(rows[1]['url'],
                         'https://github.com/o/r/releases/tag/v0.2')

    def test_releases_follow_pages(self):
        page1 = [dict(REL[0], tag_name='t%d' % i,
                      published_at='2022-01-01T00:00:%02dZ' % (i % 60))
                 for i in range(100)]
        self.seed('repos/o/r/releases?per_page=100&page=1', page1)
        self.seed('repos/o/r/releases?per_page=100&page=2', REL)
        rows = gh_api.releases('o/r', self.d, offline=True)
        self.assertEqual(len(rows), 102)

    def test_empty_release_list(self):
        self.seed('repos/o/r/releases?per_page=100&page=1', [])
        self.assertEqual(gh_api.releases('o/r', self.d, offline=True),
                         [])

    def test_tsv_row(self):
        self.seed('repos/o/r/releases?per_page=100&page=1', REL)
        rows = gh_api.releases('o/r', self.d, offline=True)
        self.assertEqual(gh_api.tsv_row('r', rows[1]),
                         'r\tv0.2\t2021-03-04\t\t'
                         'https://github.com/o/r/releases/tag/v0.2')
        self.assertIn('\t(pre-release)\t', gh_api.tsv_row('r', rows[0]))


if __name__ == '__main__':
    unittest.main()
