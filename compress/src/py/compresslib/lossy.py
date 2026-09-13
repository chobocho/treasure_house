# -*- coding: utf-8 -*-
"""손실 압축 — SPEC §19.

여기까지는 한 비트도 안 버렸다. 이 모듈은 **일부러 버린다.** 버리는
자리는 딱 하나, 양자화다 — DCT 도 PNG 필터도 그 자체로는 안 버린다.
그래서 이 파일에서 손실인 것과 아닌 것을 표로 갈라 적는다.

    양자화        손실     버리는 곳은 여기 하나뿐이다
    dct8         아니다   정수 근사의 반올림만 (최대 2/255)
    jpeglite     손실     DCT → 양자화 → 지그재그 → 0런 → 허프만
    PNG 필터      **아니다**  PNG 은 손실 형식이 아니다
    adpcm        손실     IMA ADPCM, 표본당 4비트

**레지스트리에 오르는 코덱은 PNG 쪽** 이다. 왕복하는 것이 그것뿐이기
때문이다. 손실 코덱에 골든 벡터를 붙이면 부호기만 못 박는 꼴이고,
decode(encode(x)) == x 가 애초에 거짓이다.

실수는 한 번도 안 쓴다(§0.1). 코사인 행렬·양자화표·ADPCM 표는 전부
tools/gen_tables.py 가 만들고 다섯 언어를 대조한다.
"""
from compresslib import deflate, huffman, varint

DCT_SCALE = 13
DCT_ROUND = 1 << (DCT_SCALE - 1)
BLOCK = 8
PNG_WIDTH = 256          # 골든 코덱이 쓰는 행 폭 (§19.5)
PNG_BPP = 1

# DCT-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.2)
DCT = [
    2896, 2896, 2896, 2896, 2896, 2896, 2896, 2896,
    4017, 3406, 2276, 799, -799, -2276, -3406, -4017,
    3784, 1567, -1567, -3784, -3784, -1567, 1567, 3784,
    3406, -799, -4017, -2276, 2276, 4017, 799, -3406,
    2896, -2896, -2896, 2896, 2896, -2896, -2896, 2896,
    2276, -4017, 799, 3406, -3406, -799, 4017, -2276,
    1567, -3784, 3784, -1567, -1567, 3784, -3784, 1567,
    799, -2276, 3406, -4017, 4017, -3406, 2276, -799]
# DCT-TABLE-END

# JPEGQ-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.4)
JPEG_QUANT = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99]
# JPEGQ-TABLE-END

# ADPCMSTEP-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
ADPCM_STEP = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130,
    143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449,
    494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411,
    1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026,
    4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
    12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
    29794, 32767]
# ADPCMSTEP-TABLE-END

# ADPCMINDEX-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
ADPCM_INDEX = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]
# ADPCMINDEX-TABLE-END


def zigzag_order():
    """8×8 을 대각선으로 훑는 순서. 표가 아니라 규칙이라 만든다."""
    order = []
    for s in range(15):
        cells = [(x, s - x) for x in range(8) if 0 <= s - x < 8]
        if s % 2 == 1:
            cells.reverse()
        order += [y * 8 + x for x, y in cells]
    return order


ZIGZAG = zigzag_order()


# -------------------------------------------------------- 양자화
def quantise(v, q, dead_zone=False):
    """버리는 곳은 여기 하나뿐이다 (§19.3)."""
    if dead_zone:
        return -((-v) // q) if v < 0 else v // q
    if v < 0:
        return -((-v * 2 + q) // (2 * q))
    return (v * 2 + q) // (2 * q)


def dequantise(v, q):
    return v * q


# ------------------------------------------------------------------ DCT
def fdct8(block):
    """8×8 정수 DCT. 1차원 변환 두 번, 각각 반올림 (§19.2)."""
    tmp = [0] * 64
    for u in range(8):
        base = u * 8
        for y in range(8):
            s = 0
            for x in range(8):
                s += DCT[base + x] * block[x * 8 + y]
            tmp[base + y] = (s + DCT_ROUND) >> DCT_SCALE
    out = [0] * 64
    for u in range(8):
        for v in range(8):
            s = 0
            for y in range(8):
                s += DCT[v * 8 + y] * tmp[u * 8 + y]
            out[u * 8 + v] = (s + DCT_ROUND) >> DCT_SCALE
    return out


def idct8(coef):
    tmp = [0] * 64
    for x in range(8):
        for v in range(8):
            s = 0
            for u in range(8):
                s += DCT[u * 8 + x] * coef[u * 8 + v]
            tmp[x * 8 + v] = (s + DCT_ROUND) >> DCT_SCALE
    out = [0] * 64
    for x in range(8):
        for y in range(8):
            s = 0
            for v in range(8):
                s += DCT[v * 8 + y] * tmp[x * 8 + v]
            out[x * 8 + y] = (s + DCT_ROUND) >> DCT_SCALE
    return out


def quant_table(quality):
    """품질 1~100 로 JPEG 표준표를 늘리고 줄인다 (§19.4)."""
    if not 1 <= quality <= 100:
        raise ValueError('품질은 1~100 이다: %d' % quality)
    scale = 5000 // quality if quality < 50 else 200 - 2 * quality
    out = []
    for base in JPEG_QUANT:
        q = (base * scale + 50) // 100
        out.append(max(1, min(255, q)))
    return out


# ------------------------------------------------------------- jpeglite
JPEG_MAGIC = b'JL1'
EOB = 255


def jpeglite_encode(pixels, width, height, quality=50):
    """회색조 픽셀 → 우리 형식. JPEG 이 아니다 (§19.4)."""
    if width * height != len(pixels):
        raise ValueError('픽셀 수가 너비×높이와 다르다')
    if not 0 < width <= 0xFFFF or not 0 < height <= 0xFFFF:
        raise ValueError('크기가 범위를 벗어났다')
    qt = quant_table(quality)
    stream = bytearray()
    for by in range(0, height, BLOCK):
        for bx in range(0, width, BLOCK):
            block = [0] * 64
            for y in range(BLOCK):
                sy = min(by + y, height - 1)
                for x in range(BLOCK):
                    sx = min(bx + x, width - 1)
                    block[x * 8 + y] = pixels[sy * width + sx] - 128
            coef = fdct8(block)
            run = 0
            for k, idx in enumerate(ZIGZAG):
                # 양자화표는 **래스터 순서** 다. 지그재그 자리 k 가
                # 아니라 그 자리가 가리키는 래스터 위치 idx 로 찾는다.
                v = quantise(coef[idx], qt[idx], dead_zone=(k > 0))
                if v == 0 and k > 0:
                    run += 1
                    continue
                # (254, 0) 은 복호기가 254 를 건너뛰고 0 을 하나 놓으니
                # 0 이 255 개다. 254 를 빼면 한 칸 어긋난다.
                while run >= EOB:
                    stream.append(EOB - 1)
                    stream.append(0)
                    run -= EOB
                stream.append(run)
                stream += varint.put((v << 1) ^ (v >> 63) if v >= 0
                                     else ((-v) << 1) - 1)
                run = 0
            stream.append(EOB)
    head = bytearray(JPEG_MAGIC)
    head += width.to_bytes(2, 'little')
    head += height.to_bytes(2, 'little')
    head.append(quality)
    return bytes(head) + huffman.encode(bytes(stream))


def jpeglite_decode(src):
    """(픽셀, 너비, 높이). 원본과 같지 않다 — 그게 약속이다."""
    if len(src) < 8 or src[:3] != JPEG_MAGIC:
        raise ValueError('jpeglite 매직이 아니다')
    width = int.from_bytes(src[3:5], 'little')
    height = int.from_bytes(src[5:7], 'little')
    quality = src[7]
    qt = quant_table(quality)
    stream = huffman.decode(src[8:])
    pos = 0
    pixels = bytearray(width * height)
    for by in range(0, height, BLOCK):
        for bx in range(0, width, BLOCK):
            coef = [0] * 64
            k = 0
            # **끝 표시는 반드시 읽어 치운다.** k < 64 를 고리 조건
            # 으로 두면 64개가 다 실린 블록(품질 100)에서 EOB 를 안
            # 먹고 나가고, 다음 블록이 그 255 를 자기 EOB 로 읽는다.
            while True:
                if pos >= len(stream):
                    raise ValueError('계수 스트림이 잘렸다')
                run = stream[pos]
                pos += 1
                if run == EOB:
                    break
                k += run
                if k >= 64:
                    raise ValueError('0 런이 블록을 넘는다')
                u, pos = varint.get(stream, pos)
                v = -((u + 1) >> 1) if (u & 1) else (u >> 1)
                coef[ZIGZAG[k]] = dequantise(v, qt[ZIGZAG[k]])
                k += 1
            block = idct8(coef)
            for y in range(BLOCK):
                sy = by + y
                if sy >= height:
                    break
                for x in range(BLOCK):
                    sx = bx + x
                    if sx >= width:
                        break
                    p = block[x * 8 + y] + 128
                    pixels[sy * width + sx] = max(0, min(255, p))
    return bytes(pixels), width, height


# ------------------------------------------------------ PNG 필터
def paeth(a, b, c):
    """왼쪽·위·왼쪽위 중 a+b-c 에 가장 가까운 것. 동점은 a, 다음 b."""
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _filter_row(row, prev, kind, bpp):
    out = bytearray(len(row))
    for i, v in enumerate(row):
        left = row[i - bpp] if i >= bpp else 0
        up = prev[i] if i < len(prev) else 0
        near = i >= bpp and i - bpp < len(prev)
        upleft = prev[i - bpp] if near else 0
        if kind == 0:
            d = v
        elif kind == 1:
            d = v - left
        elif kind == 2:
            d = v - up
        elif kind == 3:
            d = v - ((left + up) >> 1)
        else:
            d = v - paeth(left, up, upleft)
        out[i] = d & 0xFF
    return bytes(out)


def _unfilter_row(row, prev, kind, bpp):
    out = bytearray(len(row))
    for i, d in enumerate(row):
        left = out[i - bpp] if i >= bpp else 0
        up = prev[i] if i < len(prev) else 0
        near = i >= bpp and i - bpp < len(prev)
        upleft = prev[i - bpp] if near else 0
        if kind == 0:
            v = d
        elif kind == 1:
            v = d + left
        elif kind == 2:
            v = d + up
        elif kind == 3:
            v = d + ((left + up) >> 1)
        elif kind == 4:
            v = d + paeth(left, up, upleft)
        else:
            raise ValueError('없는 필터 종류: %d' % kind)
        out[i] = v & 0xFF
    return bytes(out)


def png_filter(data, width, bpp=PNG_BPP):
    """줄마다 다섯 후보 중 절댓값 합이 가장 작은 것 (§19.5)."""
    out = bytearray()
    prev = b''
    for off in range(0, len(data), width):
        row = data[off:off + width]
        best_kind, best_row, best_score = 0, None, None
        for kind in range(5):
            cand = _filter_row(row, prev, kind, bpp)
            score = sum(b if b < 128 else 256 - b for b in cand)
            if best_score is None or score < best_score:
                best_kind, best_row, best_score = kind, cand, score
        out.append(best_kind)
        out += best_row
        prev = row
    return bytes(out)


def png_unfilter(data, width, bpp=PNG_BPP):
    out = bytearray()
    prev = b''
    pos = 0
    while pos < len(data):
        kind = data[pos]
        pos += 1
        n = min(width, len(data) - pos)
        row = _unfilter_row(data[pos:pos + n], prev, kind, bpp)
        pos += n
        out += row
        prev = row
    return bytes(out)


# ------------------------------------------------------------ 골든 코덱
def encode(src):
    """PNG 쪽 — 이 모듈에서 유일하게 왕복하는 코덱이다 (§19.1)."""
    if not src:
        return varint.put(0)
    filtered = png_filter(src, PNG_WIDTH)
    return varint.put(len(src)) + deflate.encode(filtered)


def decode(src):
    n, pos = varint.get_length(src)
    if n == 0:
        if pos != len(src):
            raise ValueError('빈 입력인데 뒤에 바이트가 있다')
        return b''
    out = png_unfilter(deflate.decode(src[pos:]), PNG_WIDTH)
    if len(out) != n:
        raise ValueError('푼 길이가 헤더와 다르다: %d != %d'
                         % (len(out), n))
    return out


# ----------------------------------------------------------- IMA ADPCM
def adpcm_encode(samples):
    """16비트 표본 → 표본당 4비트. 예측기를 안 보내는 것이 요점이다."""
    out = bytearray()
    predictor = 0
    index = 0
    half = None
    for s in samples:
        step = ADPCM_STEP[index]
        diff = s - predictor
        code = 0
        if diff < 0:
            code = 8
            diff = -diff
        mag = min(7, (diff * 4) // step)
        code |= mag
        delta = step >> 3
        if mag & 4:
            delta += step
        if mag & 2:
            delta += step >> 1
        if mag & 1:
            delta += step >> 2
        predictor += -delta if (code & 8) else delta
        predictor = max(-32768, min(32767, predictor))
        index = max(0, min(88, index + ADPCM_INDEX[code & 7]))
        if half is None:
            half = code
        else:
            out.append((half << 4) | code)
            half = None
    if half is not None:
        out.append(half << 4)
    return bytes(out)


def adpcm_decode(data, count):
    out = []
    predictor = 0
    index = 0
    for i in range(count):
        byte = data[i >> 1]
        code = (byte >> 4) if (i & 1) == 0 else (byte & 0x0F)
        step = ADPCM_STEP[index]
        mag = code & 7
        delta = step >> 3
        if mag & 4:
            delta += step
        if mag & 2:
            delta += step >> 1
        if mag & 1:
            delta += step >> 2
        predictor += -delta if (code & 8) else delta
        predictor = max(-32768, min(32767, predictor))
        index = max(0, min(88, index + ADPCM_INDEX[code & 7]))
        out.append(predictor)
    return out
