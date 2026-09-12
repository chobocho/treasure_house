package compresslib;

import java.util.Arrays;

/**
 * 버로우즈–휠러 변환 — SPEC §9.
 *
 * <p>배가 늘리기 정렬. 키를 rank[i]*(m+1) + rank[i+k] 로 눌러 담는데,
 * <b>첫 회의 rank 를 바이트 값 그대로 쓰면 안 된다</b> — 곱수 m+1 이
 * 255 보다 작아져 자리가 겹친다. 0..(서로 다른 값 수-1) 로 먼저
 * 압축한다. 같은 회전이 여럿이면 순서는 시작 위치 오름차순 — 안정
 * 정렬이 필요하다.
 *
 * <p>자바의 기본 정렬은 객체 배열에서만 안정이다. int[] 를 sort 하면
 * 듀얼피벗 퀵소트라 안정이 아니므로, 인덱스를 Integer[] 로 담아
 * 정렬한다.
 */
public final class Bwt {
  public static final int BLOCK = 1 << 16;
  public static final int ALPHABET = 256;

  private Bwt() {}

  /** L 열은 돌려주고 primary 는 out 배열의 0번에 담는다. */
  public static byte[] transformBlock(byte[] block, int[] primaryOut) {
    int m = block.length;
    primaryOut[0] = 0;
    if (m == 0) {
      return new byte[0];
    }
    int[] order = new int[ALPHABET];
    for (byte c : block) {
      order[c & 0xFF] = 1;
    }
    int next = 0;
    for (int i = 0; i < ALPHABET; i++) {
      if (order[i] > 0) {
        order[i] = next++;
      }
    }
    long[] rank = new long[m];
    for (int i = 0; i < m; i++) {
      rank[i] = order[block[i] & 0xFF];
    }
    Integer[] sa = new Integer[m];
    for (int i = 0; i < m; i++) {
      sa[i] = i;
    }
    long[] keys = new long[m];
    long[] newRank = new long[m];
    long mul = (long) m + 1;
    for (int k = 1; ; k *= 2) {
      for (int i = 0; i < m; i++) {
        keys[i] = rank[i] * mul + rank[(i + k) % m];
      }
      final long[] sortKeys = keys;
      Arrays.sort(sa, (a, b) -> Long.compare(sortKeys[a], sortKeys[b]));
      long r = 0;
      newRank[sa[0]] = 0;
      for (int j = 1; j < m; j++) {
        if (keys[sa[j]] != keys[sa[j - 1]]) {
          r++;
        }
        newRank[sa[j]] = r;
      }
      System.arraycopy(newRank, 0, rank, 0, m);
      if (r == m - 1 || k >= m) {
        break;
      }
    }
    byte[] l = new byte[m];
    for (int j = 0; j < m; j++) {
      int i = sa[j];
      l[j] = block[(i + m - 1) % m];
      if (i == 0) {
        primaryOut[0] = j;
      }
    }
    return l;
  }

  public static byte[] inverseBlock(byte[] l, int primary) {
    int m = l.length;
    if (m == 0) {
      return new byte[0];
    }
    if (primary < 0 || primary >= m) {
      throw CodecException.of("primary 가 범위 밖이다: %d", primary);
    }
    int[] count = new int[ALPHABET];
    int[] first = new int[ALPHABET];
    int[] occ = new int[ALPHABET];
    for (byte c : l) {
      count[c & 0xFF]++;
    }
    int total = 0;
    for (int c = 0; c < ALPHABET; c++) {
      first[c] = total;
      total += count[c];
    }
    // nxt 는 LF 의 역치환이다. LF 로 걸으면 원문이 거꾸로 나오고,
    // nxt 로 걸으면 바로 나온다.
    int[] nxt = new int[m];
    for (int i = 0; i < m; i++) {
      int c = l[i] & 0xFF;
      nxt[first[c] + occ[c]] = i;
      occ[c]++;
    }
    byte[] out = new byte[m];
    int i = primary;
    for (int step = 0; step < m; step++) {
      i = nxt[i];
      out[step] = l[i];
    }
    return out;
  }

  public static byte[] encode(byte[] src) {
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    int[] primary = new int[1];
    for (int off = 0; off < src.length; off += BLOCK) {
      int end = Math.min(off + BLOCK, src.length);
      byte[] block = Arrays.copyOfRange(src, off, end);
      byte[] l = transformBlock(block, primary);
      int p = primary[0];
      out.push(p & 0xFF);
      out.push((p >>> 8) & 0xFF);
      out.push((p >>> 16) & 0xFF);
      out.push((p >>> 24) & 0xFF);
      out.extend(l);
    }
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    int n = h[0];
    int pos = h[1];
    ByteBuf out = new ByteBuf();
    int left = n;
    while (left > 0) {
      int m = Math.min(BLOCK, left);
      if (pos + 4 + m > src.length) {
        throw new CodecException("블록이 잘렸다");
      }
      int primary = (src[pos] & 0xFF)
          | ((src[pos + 1] & 0xFF) << 8)
          | ((src[pos + 2] & 0xFF) << 16)
          | ((src[pos + 3] & 0xFF) << 24);
      pos += 4;
      byte[] l = Arrays.copyOfRange(src, pos, pos + m);
      out.extend(inverseBlock(l, primary));
      pos += m;
      left -= m;
    }
    if (pos != src.length) {
      throw new CodecException("뒤에 남은 바이트가 있다");
    }
    return out.bytes();
  }
}
