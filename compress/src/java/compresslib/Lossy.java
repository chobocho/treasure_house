package compresslib;

/**
 * 손실 압축 — SPEC §19.
 *
 * <p>여기까지는 한 비트도 안 버렸다. 이 모듈은 <b>일부러 버린다.</b>
 * 버리는 자리는 딱 하나, 양자화다 — DCT 도 PNG 필터도 그 자체로는
 * 아무것도 안 버린다.
 *
 * <p><b>레지스트리에 오르는 코덱은 PNG 쪽</b> 이다. 왕복하는 것이
 * 그것뿐이기 때문이다. 손실 코덱에 골든 벡터를 붙이면 "같은 그림"이
 * 아니라 "같은 부호기"만 못 박는 꼴이 된다.
 */
public final class Lossy {
  public static final int DCT_SCALE = 13;
  public static final int DCT_ROUND = 1 << (DCT_SCALE - 1);
  public static final int BLOCK = 8;
  public static final int PNG_WIDTH = 256;  // 골든 코덱의 행 폭 (§19.5)
  public static final int PNG_BPP = 1;
  public static final int EOB = 255;

  // DCT-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.2)
  public static final int[] DCT = {
    2896, 2896, 2896, 2896, 2896, 2896, 2896, 2896,
    4017, 3406, 2276, 799, -799, -2276, -3406, -4017,
    3784, 1567, -1567, -3784, -3784, -1567, 1567, 3784,
    3406, -799, -4017, -2276, 2276, 4017, 799, -3406,
    2896, -2896, -2896, 2896, 2896, -2896, -2896, 2896,
    2276, -4017, 799, 3406, -3406, -799, 4017, -2276,
    1567, -3784, 3784, -1567, -1567, 3784, -3784, 1567,
    799, -2276, 3406, -4017, 4017, -3406, 2276, -799};
  // DCT-TABLE-END

  // JPEGQ-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.4)
  public static final int[] JPEG_QUANT = {
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99};
  // JPEGQ-TABLE-END

  // ADPCMSTEP-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
  public static final int[] ADPCM_STEP = {
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130,
    143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449,
    494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411,
    1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026,
    4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
    12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
    29794, 32767};
  // ADPCMSTEP-TABLE-END

  // ADPCMINDEX-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
  public static final int[] ADPCM_INDEX = {-1, -1, -1, -1, 2, 4, 6, 8,
                                           -1, -1, -1, -1, 2, 4, 6, 8};
  // ADPCMINDEX-TABLE-END

  /** 8×8 을 대각선으로 훑는 순서. 표가 아니라 규칙이라 만든다. */
  public static final int[] ZIGZAG = buildZigzag();

  private static int[] buildZigzag() {
    int[] out = new int[64];
    int n = 0;
    for (int s = 0; s < 15; s++) {
      int[] xs = new int[8];
      int c = 0;
      for (int x = 0; x < 8; x++) {
        int y = s - x;
        if (y >= 0 && y < 8) {
          xs[c++] = x;
        }
      }
      for (int i = 0; i < c; i++) {
        int x = (s % 2 == 1) ? xs[c - 1 - i] : xs[i];
        out[n++] = (s - x) * 8 + x;
      }
    }
    return out;
  }

  private Lossy() {
  }

  /** 버리는 곳은 여기 하나뿐이다 (§19.3). */
  public static int quantise(int v, int q, boolean deadZone) {
    if (deadZone) {
      return v < 0 ? -((-v) / q) : v / q;
    }
    if (v < 0) {
      return -(((-v) * 2 + q) / (2 * q));
    }
    return (v * 2 + q) / (2 * q);
  }

  public static int dequantise(int v, int q) {
    return v * q;
  }

  /** 8×8 정수 DCT. 1차원 변환 두 번, 각각 반올림 (§19.2). */
  public static int[] fdct8(int[] block) {
    int[] tmp = new int[64];
    int[] out = new int[64];
    for (int u = 0; u < 8; u++) {
      for (int y = 0; y < 8; y++) {
        int s = 0;
        for (int x = 0; x < 8; x++) {
          s += DCT[u * 8 + x] * block[x * 8 + y];
        }
        tmp[u * 8 + y] = (s + DCT_ROUND) >> DCT_SCALE;
      }
    }
    for (int u = 0; u < 8; u++) {
      for (int v = 0; v < 8; v++) {
        int s = 0;
        for (int y = 0; y < 8; y++) {
          s += DCT[v * 8 + y] * tmp[u * 8 + y];
        }
        out[u * 8 + v] = (s + DCT_ROUND) >> DCT_SCALE;
      }
    }
    return out;
  }

  public static int[] idct8(int[] coef) {
    int[] tmp = new int[64];
    int[] out = new int[64];
    for (int x = 0; x < 8; x++) {
      for (int v = 0; v < 8; v++) {
        int s = 0;
        for (int u = 0; u < 8; u++) {
          s += DCT[u * 8 + x] * coef[u * 8 + v];
        }
        tmp[x * 8 + v] = (s + DCT_ROUND) >> DCT_SCALE;
      }
    }
    for (int x = 0; x < 8; x++) {
      for (int y = 0; y < 8; y++) {
        int s = 0;
        for (int v = 0; v < 8; v++) {
          s += DCT[v * 8 + y] * tmp[x * 8 + v];
        }
        out[x * 8 + y] = (s + DCT_ROUND) >> DCT_SCALE;
      }
    }
    return out;
  }

  /** 품질 1~100 으로 JPEG 표준표를 늘리고 줄인다 (§19.4). */
  public static int[] quantTable(int quality) {
    if (quality < 1 || quality > 100) {
      throw new CodecException("품질은 1~100 이다: " + quality);
    }
    int scale = quality < 50 ? 5000 / quality : 200 - 2 * quality;
    int[] out = new int[64];
    for (int i = 0; i < 64; i++) {
      int v = (JPEG_QUANT[i] * scale + 50) / 100;
      out[i] = Math.max(1, Math.min(255, v));
    }
    return out;
  }

  /** jpeglite — 우리 형식이다. JPEG 이 아니다 (§19.4). */
  public static byte[] jpegliteEncode(byte[] pixels, int width,
                                      int height, int quality) {
    if (width * height != pixels.length) {
      throw new CodecException("픽셀 수가 너비×높이와 다르다");
    }
    if (width <= 0 || height <= 0 || width > 0xFFFF
        || height > 0xFFFF) {
      throw new CodecException("크기가 범위를 벗어났다");
    }
    int[] qt = quantTable(quality);
    ByteBuf stream = new ByteBuf();
    for (int by = 0; by < height; by += BLOCK) {
      for (int bx = 0; bx < width; bx += BLOCK) {
        int[] block = new int[64];
        for (int y = 0; y < BLOCK; y++) {
          int sy = Math.min(by + y, height - 1);
          for (int x = 0; x < BLOCK; x++) {
            int sx = Math.min(bx + x, width - 1);
            block[x * 8 + y] = (pixels[sy * width + sx] & 0xFF) - 128;
          }
        }
        int[] coef = fdct8(block);
        int run = 0;
        for (int k = 0; k < 64; k++) {
          int idx = ZIGZAG[k];
          int v = quantise(coef[idx], qt[idx], k > 0);
          if (v == 0 && k > 0) {
            run++;
            continue;
          }
          while (run >= EOB) {
            stream.push(EOB - 1);
            stream.push(0);
            run -= EOB - 1;
          }
          stream.push(run);
          long z = v >= 0 ? (long) v * 2 : (long) (-v) * 2 - 1;
          Varint.put(stream, z);
          run = 0;
        }
        stream.push(EOB);
      }
    }
    ByteBuf out = new ByteBuf();
    out.push(0x4A);
    out.push(0x4C);
    out.push(0x31);
    out.push(width & 0xFF);
    out.push(width >>> 8);
    out.push(height & 0xFF);
    out.push(height >>> 8);
    out.push(quality);
    out.extend(Huffman.encode(stream.bytes()));
    return out.bytes();
  }

  /** 푼 그림. 원본과 같지 않다 — 그게 이 형식의 약속이다. */
  public static final class Image {
    public final byte[] pixels;
    public final int width;
    public final int height;

    Image(byte[] pixels, int width, int height) {
      this.pixels = pixels;
      this.width = width;
      this.height = height;
    }
  }

  public static Image jpegliteDecode(byte[] src) {
    if (src.length < 8 || (src[0] & 0xFF) != 0x4A
        || (src[1] & 0xFF) != 0x4C || (src[2] & 0xFF) != 0x31) {
      throw new CodecException("jpeglite 매직이 아니다");
    }
    int width = (src[3] & 0xFF) | ((src[4] & 0xFF) << 8);
    int height = (src[5] & 0xFF) | ((src[6] & 0xFF) << 8);
    int[] qt = quantTable(src[7] & 0xFF);
    byte[] body = new byte[src.length - 8];
    System.arraycopy(src, 8, body, 0, body.length);
    byte[] stream = Huffman.decode(body);
    int pos = 0;
    byte[] pixels = new byte[width * height];
    for (int by = 0; by < height; by += BLOCK) {
      for (int bx = 0; bx < width; bx += BLOCK) {
        int[] coef = new int[64];
        int k = 0;
        // 끝 표시는 반드시 읽어 치운다 — 64개가 다 실린 블록에서
        // 안 먹고 나가면 다음 블록이 그 255 를 자기 EOB 로 읽는다.
        while (true) {
          if (pos >= stream.length) {
            throw new CodecException("계수 스트림이 잘렸다");
          }
          int run = stream[pos++] & 0xFF;
          if (run == EOB) {
            break;
          }
          k += run;
          if (k >= 64) {
            throw new CodecException("0 런이 블록을 넘는다");
          }
          long[] got = Varint.get(stream, pos);
          pos = (int) got[1];
          long z = got[0];
          int v = (z & 1) != 0 ? (int) (-((z + 1) / 2)) : (int) (z / 2);
          coef[ZIGZAG[k]] = dequantise(v, qt[ZIGZAG[k]]);
          k++;
        }
        int[] block = idct8(coef);
        for (int y = 0; y < BLOCK; y++) {
          int sy = by + y;
          if (sy >= height) {
            break;
          }
          for (int x = 0; x < BLOCK; x++) {
            int sx = bx + x;
            if (sx >= width) {
              break;
            }
            int p = block[x * 8 + y] + 128;
            int c = Math.max(0, Math.min(255, p));
            pixels[sy * width + sx] = (byte) c;
          }
        }
      }
    }
    return new Image(pixels, width, height);
  }

  /** 왼쪽·위·왼쪽위 중 a+b-c 에 가장 가까운 것. 동점은 a, 다음 b. */
  public static int paeth(int a, int b, int c) {
    int p = a + b - c;
    int pa = Math.abs(p - a);
    int pb = Math.abs(p - b);
    int pc = Math.abs(p - c);
    if (pa <= pb && pa <= pc) {
      return a;
    }
    if (pb <= pc) {
      return b;
    }
    return c;
  }

  private static byte[] filterRow(byte[] row, int from, int to,
                                  byte[] prev, int kind, int bpp) {
    int n = to - from;
    byte[] out = new byte[n];
    for (int i = 0; i < n; i++) {
      int v = row[from + i] & 0xFF;
      int left = i >= bpp ? (row[from + i - bpp] & 0xFF) : 0;
      int up = i < prev.length ? (prev[i] & 0xFF) : 0;
      int ul = (i >= bpp && i - bpp < prev.length)
          ? (prev[i - bpp] & 0xFF) : 0;
      int d;
      if (kind == 0) {
        d = v;
      } else if (kind == 1) {
        d = v - left;
      } else if (kind == 2) {
        d = v - up;
      } else if (kind == 3) {
        d = v - ((left + up) >> 1);
      } else {
        d = v - paeth(left, up, ul);
      }
      out[i] = (byte) d;
    }
    return out;
  }

  private static byte[] unfilterRow(byte[] row, int from, int to,
                                    byte[] prev, int kind, int bpp) {
    int n = to - from;
    byte[] out = new byte[n];
    for (int i = 0; i < n; i++) {
      int d = row[from + i] & 0xFF;
      int left = i >= bpp ? (out[i - bpp] & 0xFF) : 0;
      int up = i < prev.length ? (prev[i] & 0xFF) : 0;
      int ul = (i >= bpp && i - bpp < prev.length)
          ? (prev[i - bpp] & 0xFF) : 0;
      int v;
      if (kind == 0) {
        v = d;
      } else if (kind == 1) {
        v = d + left;
      } else if (kind == 2) {
        v = d + up;
      } else if (kind == 3) {
        v = d + ((left + up) >> 1);
      } else if (kind == 4) {
        v = d + paeth(left, up, ul);
      } else {
        throw new CodecException("없는 필터 종류: " + kind);
      }
      out[i] = (byte) v;
    }
    return out;
  }

  /** 줄마다 다섯 후보 중 절댓값 합이 가장 작은 것을 고른다 (§19.5). */
  public static byte[] pngFilter(byte[] data, int width, int bpp) {
    ByteBuf out = new ByteBuf();
    byte[] prev = new byte[0];
    for (int off = 0; off < data.length; off += width) {
      int end = Math.min(off + width, data.length);
      int bestKind = 0;
      byte[] bestRow = new byte[0];
      int bestScore = -1;
      for (int kind = 0; kind < 5; kind++) {
        byte[] cand = filterRow(data, off, end, prev, kind, bpp);
        int score = 0;
        for (byte b : cand) {
          int u = b & 0xFF;
          score += u < 128 ? u : 256 - u;
        }
        if (bestScore < 0 || score < bestScore) {
          bestKind = kind;
          bestRow = cand;
          bestScore = score;
        }
      }
      out.push(bestKind);
      out.extend(bestRow);
      prev = new byte[end - off];
      System.arraycopy(data, off, prev, 0, end - off);
    }
    return out.bytes();
  }

  public static byte[] pngUnfilter(byte[] data, int width, int bpp) {
    ByteBuf out = new ByteBuf();
    byte[] prev = new byte[0];
    int pos = 0;
    while (pos < data.length) {
      int kind = data[pos++] & 0xFF;
      int n = Math.min(width, data.length - pos);
      byte[] row = unfilterRow(data, pos, pos + n, prev, kind, bpp);
      pos += n;
      out.extend(row);
      prev = row;
    }
    return out.bytes();
  }

  /** 골든 코덱 — 이 모듈에서 유일하게 왕복한다 (§19.1). */
  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(Deflate.encode(pngFilter(src, PNG_WIDTH, PNG_BPP)));
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] head = Varint.getLength(src, 0);
    int n = head[0];
    int pos = head[1];
    if (n == 0) {
      if (pos != src.length) {
        throw new CodecException("빈 입력인데 뒤에 바이트가 있다");
      }
      return new byte[0];
    }
    byte[] body = new byte[src.length - pos];
    System.arraycopy(src, pos, body, 0, body.length);
    byte[] out = pngUnfilter(Deflate.decode(body), PNG_WIDTH, PNG_BPP);
    if (out.length != n) {
      throw new CodecException("푼 길이가 헤더와 다르다: " + out.length
          + " != " + n);
    }
    return out;
  }

  /** IMA ADPCM — 예측기를 안 보내는 것이 요점이다 (§19.6). */
  public static byte[] adpcmEncode(int[] samples) {
    ByteBuf out = new ByteBuf();
    int predictor = 0;
    int index = 0;
    int half = -1;
    for (int s : samples) {
      int step = ADPCM_STEP[index];
      int diff = s - predictor;
      int code = 0;
      if (diff < 0) {
        code = 8;
        diff = -diff;
      }
      int mag = Math.min(7, (diff * 4) / step);
      code |= mag;
      int delta = step >> 3;
      if ((mag & 4) != 0) {
        delta += step;
      }
      if ((mag & 2) != 0) {
        delta += step >> 1;
      }
      if ((mag & 1) != 0) {
        delta += step >> 2;
      }
      predictor += (code & 8) != 0 ? -delta : delta;
      predictor = Math.max(-32768, Math.min(32767, predictor));
      index = Math.max(0, Math.min(88, index + ADPCM_INDEX[code & 7]));
      if (half < 0) {
        half = code;
      } else {
        out.push((half << 4) | code);
        half = -1;
      }
    }
    if (half >= 0) {
      out.push(half << 4);
    }
    return out.bytes();
  }

  public static int[] adpcmDecode(byte[] data, int count) {
    int[] out = new int[count];
    int predictor = 0;
    int index = 0;
    for (int i = 0; i < count; i++) {
      if (i / 2 >= data.length) {
        throw new CodecException("ADPCM 스트림이 잘렸다");
      }
      int b = data[i / 2] & 0xFF;
      int code = (i % 2 == 0) ? (b >> 4) : (b & 0x0F);
      int step = ADPCM_STEP[index];
      int mag = code & 7;
      int delta = step >> 3;
      if ((mag & 4) != 0) {
        delta += step;
      }
      if ((mag & 2) != 0) {
        delta += step >> 1;
      }
      if ((mag & 1) != 0) {
        delta += step >> 2;
      }
      predictor += (code & 8) != 0 ? -delta : delta;
      predictor = Math.max(-32768, Math.min(32767, predictor));
      index = Math.max(0, Math.min(88, index + ADPCM_INDEX[code & 7]));
      out[i] = predictor;
    }
    return out;
  }
}
