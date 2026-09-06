# -*- coding: utf-8 -*-
"""PPM(P6) → PNG. 표준 라이브러리 zlib 만 쓴다.

   덱에 화면을 싣기 위한 도구다. 외부 라이브러리를 쓰지 않는 것은 이 저장소의
   규칙이기도 하고, PNG 가 '필터 바이트 + zlib' 만으로 만들어진다는 사실을
   보여 주기에도 좋다.
"""
import binascii, io, os, struct, sys, zlib


def read_ppm(path):
    data = io.open(path, 'rb').read()
    if not data.startswith(b'P6'):
        raise ValueError('P6 PPM 이 아니다')
    fields, pos = [], 2
    while len(fields) < 3:
        while pos < len(data) and data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b'#':
            while data[pos:pos + 1] not in (b'\n', b''):
                pos += 1
            continue
        start = pos
        while pos < len(data) and not data[pos:pos + 1].isspace():
            pos += 1
        fields.append(int(data[start:pos]))
    pos += 1
    w, h, _mx = fields
    return w, h, data[pos:pos + w * h * 3]


def write_png(path, w, h, rgb, scale=1):
    if scale > 1:
        big = bytearray()
        for y in range(h):
            row = bytearray()
            for x in range(w):
                px = rgb[(y * w + x) * 3:(y * w + x) * 3 + 3]
                row.extend(px * scale)
            for _ in range(scale):
                big.extend(row)
        rgb = bytes(big)
        w, h = w * scale, h * scale
    raw = bytearray()
    for y in range(h):
        raw.append(0)                       # 필터 0 = None
        raw.extend(rgb[y * w * 3:(y + 1) * w * 3])

    def chunk(tag, payload):
        return (struct.pack('>I', len(payload)) + tag + payload +
                struct.pack('>I', binascii.crc32(tag + payload) & 0xFFFFFFFF))

    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + chunk(b'IEND', b''))
    io.open(path, 'wb').write(png)
    return len(png)


def main(argv):
    src = argv[1]
    dst = argv[2] if len(argv) > 2 else os.path.splitext(src)[0] + '.png'
    scale = int(argv[3]) if len(argv) > 3 else 1
    w, h, rgb = read_ppm(src)
    n = write_png(dst, w, h, rgb, scale)
    print('%s → %s  %dx%d ×%d  %d바이트' % (src, dst, w, h, scale, n))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
