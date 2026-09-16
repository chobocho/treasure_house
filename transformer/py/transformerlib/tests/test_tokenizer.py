# -*- coding: utf-8 -*-
"""tokenizer 의 증인 시험 — SPEC.md §5 (PLAN.md §3.1 표 5행).

토크나이저는 정수 산출물이라 허용 오차가 0 이다. 같은 말뭉치에서 같은
병합, 같은 토큰, 같은 .bin 바이트가 나와야 C 가 따라올 수 있다.
"""
import io
import os
import tempfile
import unittest

from transformerlib import tokenizer as tk

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(HERE))), 'corpus')


def corpus_files():
    out = []
    for sub in ('ko', 'en', 'tasks'):
        d = os.path.join(CORPUS, sub)
        out += [os.path.join(d, n) for n in sorted(os.listdir(d))]
    return out


def read(p):
    return io.open(p, encoding='utf-8', newline='').read()


class TestPretokenizer(unittest.TestCase):
    def test_classes(self):
        want = {' ': 'S', '\n': 'W', '\t': 'W', '7': 'D', 'a': 'L',
                'Z': 'L', '한': 'L', 'é': 'L', ',': 'P', '~': 'P',
                '—': 'P', '。': 'P', '！': 'P',
                '\x00': 'P'}
        for c, k in want.items():
            self.assertEqual(tk.char_class(c), k, repr(c))

    def test_decision_table(self):
        cases = [
            ('안녕하세요 세계', ['안녕하세요', ' 세계']),
            ('a  b', ['a', ' ', ' b']),
            ('x\n\ny', ['x', '\n\n', 'y']),
            ('12.5%', ['12', '.', '5', '%']),
            ('hi ,ok', ['hi', ' ,', 'ok']),
            ('a \n b', ['a', ' \n', ' b']),
            ('end  ', ['end', '  ']),
            ('123+456=7590\n', ['123', '+', '456', '=', '7590', '\n']),
            ('', []),
        ]
        for text, want in cases:
            self.assertEqual(tk.pretokenize(text), want, repr(text))

    def test_chunks_rebuild_every_corpus_file(self):
        for p in corpus_files()[:12]:
            t = read(p)
            self.assertEqual(''.join(tk.pretokenize(t)), t, p)


class TestBpe(unittest.TestCase):
    def test_tie_break_takes_smaller_pair(self):
        """ab 와 cd 가 둘 다 2번 — (97,98) 이 (99,100) 보다 작다."""
        vocab, merges = tk.train_bpe('abab cdcd', 300)
        self.assertEqual(merges, [(97, 98), (99, 100)])
        self.assertEqual(vocab[256], b'ab')
        self.assertEqual(vocab[257], b'cd')
        self.assertEqual(len(vocab), 258)       # 개수 < 2 에서 멈췄다

    def test_merge_is_left_to_right_non_overlapping(self):
        vocab, merges = tk.train_bpe('aaa aaa', 257)
        self.assertEqual(merges, [(97, 97)])
        tok = tk.Tokenizer(vocab, merges)
        # 'aaa' → [aa, a] (왼쪽부터 겹치지 않게), ' aaa' → [' ', aa, a]
        self.assertEqual(tok.encode('aaa aaa'),
                         [256, 97, 32, 256, 97])

    def test_merges_never_cross_chunks(self):
        vocab, merges = tk.train_bpe('a b a b a b', 300)
        for l, r in merges:
            joined = vocab[l] + vocab[r]
            self.assertEqual(len(tk.pretokenize(joined.decode())), 1)

    def test_deterministic(self):
        text = read(corpus_files()[0])
        self.assertEqual(tk.train_bpe(text, 300),
                         tk.train_bpe(text, 300))

    def test_korean_syllable_is_three_bytes(self):
        tok = tk.Tokenizer(tk.byte_vocab(), [])
        self.assertEqual(tok.encode('한'), [0xED, 0x95, 0x9C])
        self.assertEqual(tok.decode([0xED, 0x95, 0x9C]), '한')

    def test_round_trip_every_corpus_file(self):
        ko = ''.join(read(p) for p in corpus_files()[:6])
        vocab, merges = tk.train_bpe(ko, 400)
        tok = tk.Tokenizer(vocab, merges)
        for p in corpus_files():
            t = read(p)
            ids = tok.encode(t)
            self.assertEqual(tok.decode(ids), t, p)
            self.assertTrue(all(0 <= i < len(vocab) for i in ids))

    def test_merges_shorten(self):
        text = read(corpus_files()[0])
        vocab, merges = tk.train_bpe(text, 400)
        n_bytes = len(text.encode('utf-8'))
        n_tok = len(tk.Tokenizer(vocab, merges).encode(text))
        self.assertLess(n_tok, n_bytes)


class TestCharVocab(unittest.TestCase):
    def test_char_vocab_is_sorted_used_bytes(self):
        vocab = tk.char_vocab('b+a=ab\n')
        self.assertEqual(vocab, [b'\n', b'+', b'=', b'a', b'b'])
        tok = tk.Tokenizer(vocab, [])
        self.assertEqual(tok.encode('ab+\n'), [3, 4, 1, 0])

    def test_unknown_byte_fails_loudly(self):
        tok = tk.Tokenizer(tk.char_vocab('abc'), [])
        with self.assertRaises(ValueError):
            tok.encode('abd')


class TestFiles(unittest.TestCase):
    def test_save_load_round_trip(self):
        vocab, merges = tk.train_bpe('abab cdcd 한글 한글', 300)
        with tempfile.TemporaryDirectory() as d:
            prefix = os.path.join(d, 'x')
            tk.save(prefix, vocab, merges)
            v2, m2 = tk.load(prefix)
            self.assertEqual((v2, m2), (vocab, merges))
            # 모든 짝이 2번씩으로 동률이라 가장 작은 짝 (32, 237) =
            # 공백 + '한' 의 첫 바이트 0xED 가 먼저 합쳐진다
            line = read(prefix + '.vocab').split('\n')[256]
            self.assertEqual(line, '256\t20ed')
            self.assertEqual(read(prefix + '.merges').split('\n')[0],
                             '32\t237')

    def test_bin_is_uint16_little_endian(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 't.bin')
            tk.write_bin(p, [1, 258, 65535])
            self.assertEqual(io.open(p, 'rb').read(),
                             b'\x01\x00\x02\x01\xff\xff')
            self.assertEqual(tk.read_bin(p), [1, 258, 65535])
            with self.assertRaises(ValueError):
                tk.write_bin(p, [65536])


if __name__ == '__main__':
    unittest.main()
