package compresslib;

import java.util.Arrays;

/**
 * LZ4 — SPEC §14.
 *
 * <p>LZ77 인데 <b>엔트로피 부호가 아예 없다.</b> 리터럴과 일치를
 * 바이트로 그냥 적는다. DEFLATE 보다 덜 줄고 몇 배 빨리 풀린다.
 *
 * <p>꼬리 규칙 둘: 마지막 5바이트는 반드시 리터럴, 일치는 끝에서
 * 12바이트 안쪽에서 시작 금지. 지키지 않으면 진짜 lz4 가 거절한다.
 */
public final class Lz4Block {
  public static final int MIN_MATCH = 4;
  public static final int LAST_LITERALS = 5;
  public static final int MF_LIMIT = 12;
  public static final int HASH_LOG = 12;
  public static final int HASH_SIZE = 1 << HASH_LOG;
  public static final long HASH_MUL = 2654435761L;
  public static final int MAX_OFFSET = 65535;

  private Lz4Block() {}

  public static void putLsic(ByteBuf out, int v) {
    int left = v;
    while (left >= 255) {
      out.push(255);
      left -= 255;
    }
    out.push(left);
  }

  /**
   * 고리를 묶는 것은 입력 자신이다 — 이어짐 바이트가 남은 것보다
   * 많을 수 없다. 고정 상한은 솔깃하고 틀린다 (SPEC §14.3).
   */
  public static int[] getLsic(byte[] src, int pos) {
    long total = 0;
    int at = pos;
    while (at < src.length) {
      int b = src[at++] & 0xFF;
      total += b;
      if (b != 255) {
        if (total > Varint.MAX_LENGTH) {
          throw new CodecException("LSIC 값이 너무 크다");
        }
        return new int[] {(int) total, at};
      }
    }
    throw new CodecException("LSIC 가 잘렸다");
  }

  static int hash4(byte[] s, int i) {
    long v = (s[i] & 0xFFL) | ((s[i + 1] & 0xFFL) << 8)
        | ((s[i + 2] & 0xFFL) << 16) | ((s[i + 3] & 0xFFL) << 24);
    return (int) (((v * HASH_MUL) & 0xFFFFFFFFL) >>> (32 - HASH_LOG));
  }

  static boolean same4(byte[] s, int a, int b) {
    return s[a] == s[b] && s[a + 1] == s[b + 1] && s[a + 2] == s[b + 2]
        && s[a + 3] == s[b + 3];
  }

  /** 시퀀스 하나. hasMatch 가 거짓이면 마지막(리터럴만) 시퀀스다. */
  static void emit(ByteBuf out, byte[] src, int from, int to,
      boolean hasMatch, int offset, int length) {
    int litLen = to - from;
    int tokenLit = Math.min(litLen, 15);
    if (!hasMatch) {
      out.push(tokenLit << 4);
      if (litLen >= 15) {
        putLsic(out, litLen - 15);
      }
      out.extend(src, from, to);
      return;
    }
    int mlCode = length - MIN_MATCH;
    int tokenMl = Math.min(mlCode, 15);
    out.push((tokenLit << 4) | tokenMl);
    if (litLen >= 15) {
      putLsic(out, litLen - 15);
    }
    out.extend(src, from, to);
    out.push(offset & 0xFF);
    out.push(offset >>> 8);
    if (mlCode >= 15) {
      putLsic(out, mlCode - 15);
    }
  }

  public static byte[] compressBlock(byte[] src) {
    int n = src.length;
    ByteBuf out = new ByteBuf();
    if (n < MF_LIMIT + 1) {
      emit(out, src, 0, n, false, 0, 0);
      return out.bytes();
    }
    int[] table = new int[HASH_SIZE];
    Arrays.fill(table, -1);
    int ip = 0;
    int anchor = 0;
    while (ip <= n - MF_LIMIT) {
      int h = hash4(src, ip);
      int ref = table[h];
      table[h] = ip;
      if (ref >= 0 && ip - ref <= MAX_OFFSET && same4(src, ref, ip)) {
        int ml = MIN_MATCH;
        int limit = n - LAST_LITERALS;
        while (ip + ml < limit && src[ref + ml] == src[ip + ml]) {
          ml++;
        }
        emit(out, src, anchor, ip, true, ip - ref, ml);
        ip += ml;
        anchor = ip;
      } else {
        ip++;
      }
    }
    emit(out, src, anchor, n, false, 0, 0);
    return out.bytes();
  }

  public static byte[] decompressBlock(byte[] block, boolean check,
      int want) {
    ByteBuf out = new ByteBuf();
    int pos = 0;
    int n = block.length;
    while (pos < n) {
      int token = block[pos++] & 0xFF;
      int litLen = token >>> 4;
      if (litLen == 15) {
        int[] r = getLsic(block, pos);
        litLen += r[0];
        pos = r[1];
      }
      if (pos + litLen > n) {
        throw new CodecException("리터럴이 잘렸다");
      }
      out.extend(block, pos, pos + litLen);
      pos += litLen;
      if (pos == n) {
        break;            // 마지막 시퀀스는 리터럴뿐이다
      }
      if (pos + 2 > n) {
        throw new CodecException("거리가 잘렸다");
      }
      int offset = (block[pos] & 0xFF) | ((block[pos + 1] & 0xFF) << 8);
      pos += 2;
      int length = token & 15;
      if (length == 15) {
        int[] r = getLsic(block, pos);
        length += r[0];
        pos = r[1];
      }
      length += MIN_MATCH;
      if (offset == 0) {
        throw new CodecException("거리 0 은 없다");
      }
      if (offset > out.size()) {
        throw CodecException.of("거리 %d 가 낸 것보다 멀다", offset);
      }
      int start = out.size() - offset;
      // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
      for (int j = 0; j < length; j++) {
        out.push(out.at(start + j));
      }
    }
    if (check && out.size() != want) {
      throw new CodecException("푼 길이가 헤더와 다르다");
    }
    return out.bytes();
  }

  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(compressBlock(src));
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    if (h[0] == 0) {
      if (h[1] != src.length) {
        throw new CodecException("빈 입력인데 뒤에 바이트가 있다");
      }
      return new byte[0];
    }
    byte[] block = Arrays.copyOfRange(src, h[1], src.length);
    return decompressBlock(block, true, h[0]);
  }

  /**
   * 진짜 lz4 명령이 쓰는 프레임을 푼다 (§14.6). 쓰지는 않는다. 내용
   * 검사합(xxHash)은 건너뛴다 — 이유는 명세에 적어 뒀다.
   */
  public static byte[] frameDecode(byte[] src) {
    if (src.length < 7 || (src[0] & 0xFF) != 0x04
        || (src[1] & 0xFF) != 0x22 || (src[2] & 0xFF) != 0x4D
        || (src[3] & 0xFF) != 0x18) {
      throw new CodecException("lz4 프레임 매직이 아니다");
    }
    int flg = src[4] & 0xFF;
    if ((flg >>> 6) != 1) {
      throw CodecException.of("모르는 프레임 판: %d", flg >>> 6);
    }
    boolean blockChecksum = (flg & 0x10) != 0;
    boolean contentSize = (flg & 0x08) != 0;
    boolean contentChecksum = (flg & 0x04) != 0;
    boolean dictId = (flg & 0x01) != 0;
    int pos = 6;
    if (contentSize) {
      pos += 8;
    }
    if (dictId) {
      pos += 4;
    }
    pos += 1;                     // 머리 검사 바이트(HC)
    ByteBuf out = new ByteBuf();
    for (;;) {
      if (pos + 4 > src.length) {
        throw new CodecException("블록 크기가 잘렸다");
      }
      long size = (src[pos] & 0xFFL) | ((src[pos + 1] & 0xFFL) << 8)
          | ((src[pos + 2] & 0xFFL) << 16)
          | ((src[pos + 3] & 0xFFL) << 24);
      pos += 4;
      if (size == 0) {
        break;
      }
      boolean stored = (size & 0x80000000L) != 0;
      size &= 0x7FFFFFFFL;
      if (pos + size > src.length) {
        throw new CodecException("블록이 잘렸다");
      }
      byte[] chunk = Arrays.copyOfRange(src, pos, pos + (int) size);
      pos += (int) size;
      if (blockChecksum) {
        pos += 4;
      }
      out.extend(stored ? chunk : decompressBlock(chunk, false, 0));
    }
    if (contentChecksum) {
      pos += 4;
    }
    return out.bytes();
  }
}
