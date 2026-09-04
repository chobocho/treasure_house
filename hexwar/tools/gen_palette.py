# -*- coding: utf-8 -*-
"""VGA 팔레트 생성 — golden/palette.txt (256줄 "r g b", 각 0..63).

   모드 13h 의 DAC 는 채널당 6비트다. 0..255 가 아니라 0..63 이라는 사실이
   도스 그래픽 코드 곳곳에 드러난다 — 팔레트 페이드가 64단계인 것도,
   회색 계조가 64개인 것도 그래서다. PPM 으로 내보낼 때만 v*255//63 로 편다.
"""
import io, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ramp(base, top, n):
    """base 색에서 top 색으로 n 단계. 도스 게임은 지형마다 이런 램프를
       16칸씩 잡아 두고 명암·안개를 팔레트 인덱스 덧셈으로 처리했다."""
    out = []
    for i in range(n):
        out.append(tuple(base[c] + (top[c] - base[c]) * i // (n - 1) for c in range(3)))
    return out


def main():
    pal = [(0, 0, 0)] * 256

    # 1..15 — EGA 16색과 같은 자리에 UI 색을 둔다
    ega = [(0, 0, 0), (0, 0, 42), (0, 42, 0), (0, 42, 42), (42, 0, 0), (42, 0, 42),
           (42, 21, 0), (42, 42, 42), (21, 21, 21), (21, 21, 63), (21, 63, 21),
           (21, 63, 63), (63, 21, 21), (63, 21, 63), (63, 63, 21), (63, 63, 63)]
    for i in range(16):
        pal[i] = ega[i]

    blocks = [
        (16,  (10, 26, 8),  (34, 55, 26)),    # 평지 — 풀색
        (32,  (4, 16, 6),   (18, 38, 16)),    # 숲
        (48,  (26, 20, 8),  (48, 40, 22)),    # 언덕
        (64,  (22, 22, 24), (52, 52, 56)),    # 산
        (80,  (4, 10, 30),  (20, 34, 60)),    # 물
        (96,  (16, 20, 10), (32, 38, 22)),    # 늪
        (112, (24, 24, 26), (55, 55, 58)),    # 도시
        (128, (28, 22, 12), (52, 44, 28)),    # 도로·모래
        (144, (24, 0, 0),   (63, 26, 20)),    # 적군 빨강
        (160, (0, 12, 30),  (26, 44, 63)),    # 청군 파랑
        (176, (30, 26, 0),  (63, 60, 20)),    # 강조 노랑
        (192, (0, 0, 0),    (63, 63, 63)),    # 회색조 64단계(안개·페이드)
    ]
    for start, base, top in blocks:
        n = 64 if start == 192 else 16
        for i, c in enumerate(ramp(base, top, n)):
            pal[start + i] = c

    p = os.path.join(BASE, 'golden', 'palette.txt')
    io.open(p, 'w', encoding='utf-8').write(
        '\n'.join('%d %d %d' % c for c in pal) + '\n')
    print('wrote %s' % p)


if __name__ == '__main__':
    main()
