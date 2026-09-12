package compresslib;

/**
 * 런 길이 부호 — SPEC §3.
 *
 * <p>정한 값 셋이 출력 바이트를 바꾼다: 문턱 3, 런 상한 128, 리터럴
 * 상한 128. 리터럴 묶음을 min(j+r, i+128) 로 자르는 것이 특히 중요하다
 * — 안 자르면 129바이트 묶음이 나오는데, 제어 바이트에 안 들어가는
 * 길이라 못 푼다.
 */
public final class Rle {
  public static final int RUN_MIN = 3;
  public static final int RUN_MAX = 128;
  public static final int LIT_MAX = 128;
  public static final int RESERVED = 128;

  private Rle() {}

  static int runAt(byte[] src, int i, int limit) {
    byte b = src[i];
    int j = i + 1;
    int end = Math.min(src.length, i + limit);
    while (j < end && src[j] == b) {
      j++;
    }
    return j - i;
  }

  public static void pack(byte[] src, ByteBuf out) {
    int i = 0;
    int n = src.length;
    while (i < n) {
      int run = runAt(src, i, RUN_MAX);
      if (run >= RUN_MIN) {
        out.push(257 - run);
        out.push(src[i] & 0xFF);
        i += run;
        continue;
      }
      int j = i;
      while (j < n && j - i < LIT_MAX) {
        int r = runAt(src, j, RUN_MAX);
        if (r >= RUN_MIN) {
          break;
        }
        j = Math.min(j + r, i + LIT_MAX);
      }
      out.push(j - i - 1);
      out.extend(src, i, j);
      i = j;
    }
  }

  /** 푼 바이트와 다음 위치. 위치는 pos[0] 으로 돌려준다. */
  public static byte[] unpack(byte[] src, int[] pos, int want) {
    ByteBuf out = new ByteBuf();
    int n = src.length;
    int p = pos[0];
    while (out.size() < want) {
      if (p >= n) {
        throw new CodecException("PackBits 가 잘렸다");
      }
      int c = src[p++] & 0xFF;
      if (c == RESERVED) {
        throw new CodecException("제어 128 은 쓰지 않는다");
      }
      if (c < RESERVED) {
        int k = c + 1;
        if (p + k > n) {
          throw new CodecException("리터럴 묶음이 잘렸다");
        }
        out.extend(src, p, p + k);
        p += k;
      } else {
        int k = 257 - c;
        if (p >= n) {
          throw new CodecException("런 묶음이 잘렸다");
        }
        for (int j = 0; j < k; j++) {
          out.push(src[p] & 0xFF);
        }
        p++;
      }
    }
    if (out.size() != want) {
      throw new CodecException("푼 길이가 헤더와 다르다");
    }
    pos[0] = p;
    return out.bytes();
  }

  public static byte[] encode(byte[] src) {
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    pack(src, out);
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    int[] pos = {h[1]};
    byte[] out = unpack(src, pos, h[0]);
    if (pos[0] != src.length) {
      throw new CodecException("뒤에 남은 바이트가 있다");
    }
    return out;
  }

  // 0런 부호 (SPEC §3.2) — bzip2 의 RUNA/RUNB. 13번 모듈이 쓴다.
  public static final int RUN_A = 0;
  public static final int RUN_B = 1;

  public static int[] zeroRunEncode(int[] syms) {
    java.util.ArrayList<Integer> out = new java.util.ArrayList<>();
    int i = 0;
    int n = syms.length;
    while (i < n) {
      if (syms[i] != 0) {
        out.add(syms[i] + 1);
        i++;
        continue;
      }
      int j = i;
      while (j < n && syms[j] == 0) {
        j++;
      }
      long length = (long) (j - i) + 1;
      while (length > 1) {
        out.add((length & 1) == 1 ? RUN_B : RUN_A);
        length >>>= 1;
      }
      i = j;
    }
    return out.stream().mapToInt(Integer::intValue).toArray();
  }

  public static int[] zeroRunDecode(int[] syms) {
    java.util.ArrayList<Integer> out = new java.util.ArrayList<>();
    int i = 0;
    int n = syms.length;
    while (i < n) {
      if (syms[i] > 1) {
        out.add(syms[i] - 1);
        i++;
        continue;
      }
      long run = 0;
      long weight = 1;
      while (i < n && syms[i] <= 1) {
        run += (long) (syms[i] + 1) * weight;
        weight <<= 1;
        i++;
      }
      for (long j = 0; j < run; j++) {
        out.add(0);
      }
    }
    return out.stream().mapToInt(Integer::intValue).toArray();
  }
}
