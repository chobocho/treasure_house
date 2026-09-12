package compresslib;

import java.util.HashMap;
import java.util.Map;

/**
 * LZ78 계열 — SPEC §7.
 *
 * <p><b>복호기는 부호기보다 항목 하나 뒤처진다.</b> 그래서 폭을 늘리는
 * 조건이 부호기는 nextFree, 복호기는 nextFree+1 이다. 이 한 칸을 틀리면
 * 사전 254번째 항목쯤부터 어긋난다 — 작은 시험은 전부 통과한다.
 */
public final class Lzw {
  public static final int CLEAR = 256;
  public static final int EOF = 257;
  public static final int FIRST_FREE = 258;
  public static final int MIN_WIDTH = 9;
  public static final int MAX_WIDTH = 12;
  public static final int DICT_CAP = 1 << MAX_WIDTH;

  private Lzw() {}

  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    BitIO.MsbWriter w = new BitIO.MsbWriter();
    // 열쇠는 (앞 부호 << 8) | 다음 바이트 — 트라이를 맵 하나로 눌러
    // 담은 것.
    Map<Integer, Integer> table = new HashMap<>();
    int nextFree = FIRST_FREE;
    int width = MIN_WIDTH;
    int cur = -1;
    for (byte raw : src) {
      int k = raw & 0xFF;
      if (cur < 0) {
        cur = k;
        continue;
      }
      Integer found = table.get((cur << 8) | k);
      if (found != null) {
        cur = found;
        continue;
      }
      w.writeBits(cur, width);
      if (nextFree == DICT_CAP) {
        w.writeBits(CLEAR, width);
        table.clear();
        nextFree = FIRST_FREE;
        width = MIN_WIDTH;
      } else {
        table.put((cur << 8) | k, nextFree++);
        // 폭 검사는 항목을 넣은 뒤에 — 다음 부호부터 넓어진다.
        if (nextFree == (1 << width) && width < MAX_WIDTH) {
          width++;
        }
      }
      cur = k;
    }
    if (cur >= 0) {
      w.writeBits(cur, width);
    }
    w.writeBits(EOF, width);
    w.flush();
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(w.bytes());
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    int n = h[0];
    if (n == 0) {
      if (h[1] != src.length) {
        throw new CodecException("빈 입력인데 뒤에 바이트가 있다");
      }
      return new byte[0];
    }
    BitIO.MsbReader r = new BitIO.MsbReader(src, h[1]);
    ByteBuf out = new ByteBuf();
    byte[][] table = new byte[DICT_CAP][];
    int nextFree = FIRST_FREE;
    int width = MIN_WIDTH;
    byte[] prev = null;
    for (;;) {
      int code = (int) r.readBits(width);
      if (code == EOF) {
        break;
      }
      if (code == CLEAR) {
        nextFree = FIRST_FREE;
        width = MIN_WIDTH;
        prev = null;
        continue;
      }
      byte[] entry;
      if (prev == null) {
        if (code >= CLEAR) {
          throw CodecException.of("첫 부호가 리터럴이 아니다: %d",
              code);
        }
        entry = new byte[] {(byte) code};
      } else if (code < 256) {
        entry = new byte[] {(byte) code};
      } else if (code < nextFree) {
        entry = table[code];
      } else if (code == nextFree) {
        // KwKwK — 부호기가 방금 만든 항목이다. 늘 prev + prev[0] 이다.
        entry = java.util.Arrays.copyOf(prev, prev.length + 1);
        entry[prev.length] = prev[0];
      } else {
        throw CodecException.of("아직 없는 부호: %d", code);
      }
      out.extend(entry);
      if (out.size() > n) {
        throw new CodecException("푼 길이가 헤더를 넘었다");
      }
      if (prev != null) {
        byte[] added = java.util.Arrays.copyOf(prev, prev.length + 1);
        added[prev.length] = entry[0];
        table[nextFree++] = added;
        // 복호기는 한 칸 뒤처져 있다. +1 이 그 보정이다.
        if (nextFree + 1 == (1 << width) && width < MAX_WIDTH) {
          width++;
        }
      }
      prev = entry;
    }
    if (out.size() != n) {
      throw CodecException.of("푼 길이가 헤더와 다르다: %d != %d",
          out.size(), n);
    }
    return out.bytes();
  }
}
