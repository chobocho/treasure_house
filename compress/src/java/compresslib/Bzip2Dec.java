package compresslib;

import java.util.ArrayList;
import java.util.List;

/**
 * bzip2 복호기 — SPEC §15.
 *
 * <p>bzip2 가 쓰는 조각은 이미 다 있다. BWT·MTF·0런·캐노니컬 허프만.
 * bzip2 가 더한 것은 <b>조립</b> 이라, 부호기는 안 만든다 — 진짜 bzip2
 * 가 만든 파일을 푸는 편이 훨씬 센 주장이다.
 *
 * <p>가장 잘 속는 자리는 CRC 다. bzip2 의 CRC-32 는 gzip 것과 다항식은
 * 같아도 <b>반사가 없다.</b> gzip 표를 그대로 쓰면 빈 입력만 맞는다
 * (§15.6).
 */
public final class Bzip2Dec {
  public static final long BLOCK_MAGIC = 0x314159265359L;
  public static final long END_MAGIC = 0x177245385090L;
  public static final int MAX_GROUPS = 6;
  public static final int GROUP_SIZE = 50;
  public static final int MAX_CODE_LEN = 20;
  private static final int RUN_B = 1;

  private Bzip2Dec() {}

  /** 반사 없는 CRC-32/BZIP2 표. 0x04C11DB7 을 위에서부터 민다. */
  private static final int[] CRC_TABLE = makeCrcTable();

  private static int[] makeCrcTable() {
    int[] t = new int[256];
    for (int i = 0; i < 256; i++) {
      int c = i << 24;
      for (int k = 0; k < 8; k++) {
        c = (c & 0x80000000) != 0 ? (c << 1) ^ 0x04C11DB7 : c << 1;
      }
      t[i] = c;
    }
    return t;
  }

  public static int crc32Bzip2(byte[] data) {
    int c = 0xFFFFFFFF;
    for (byte b : data) {
      c = CRC_TABLE[((c >>> 24) ^ (b & 0xFF)) & 0xFF] ^ (c << 8);
    }
    return c ^ 0xFFFFFFFF;
  }

  /** MSB 먼저. bzip2 는 48비트 매직이 있어 넓은 읽기가 필요하다. */
  public static final class BitReader implements BitIO.BitSource {
    private final byte[] src;
    private int pos;
    private int buf;
    private int n;

    public BitReader(byte[] src, int pos) {
      this.src = src;
      this.pos = pos;
    }

    @Override
    public int readBit() {
      if (n == 0) {
        if (pos >= src.length) {
          throw new CodecException("bzip2 스트림이 바닥났다");
        }
        buf = src[pos++] & 0xFF;
        n = 8;
      }
      n--;
      return (buf >>> n) & 1;
    }

    public long readBits(int count) {
      long v = 0;
      for (int i = 0; i < count; i++) {
        v = (v << 1) | readBit();
      }
      return v;
    }
  }

  /** 같은 바이트 넷 뒤의 한 바이트는 "더 붙일 개수" 다 (§15.5). */
  public static byte[] rle1Decode(byte[] src) {
    ByteBuf out = new ByteBuf();
    int i = 0;
    int n = src.length;
    while (i < n) {
      byte b = src[i];
      int run = 1;
      while (run < 4 && i + run < n && src[i + run] == b) {
        run++;
      }
      for (int k = 0; k < run; k++) {
        out.push(b & 0xFF);
      }
      i += run;
      if (run == 4) {
        if (i >= n) {
          throw new CodecException("RLE1 의 개수 바이트가 없다");
        }
        int more = src[i] & 0xFF;
        for (int k = 0; k < more; k++) {
          out.push(b & 0xFF);
        }
        i++;
      }
    }
    return out.bytes();
  }

  private static int[] readSymbolMap(BitReader r) {
    List<Integer> used = new ArrayList<>();
    long groups = r.readBits(16);
    for (int g = 0; g < 16; g++) {
      if ((groups & (1L << (15 - g))) != 0) {
        long bits = r.readBits(16);
        for (int k = 0; k < 16; k++) {
          if ((bits & (1L << (15 - k))) != 0) {
            used.add(g * 16 + k);
          }
        }
      }
    }
    if (used.isEmpty()) {
      throw new CodecException("기호 지도가 비었다");
    }
    return used.stream().mapToInt(Integer::intValue).toArray();
  }

  /** 단항으로 적힌 MTF 선택자. 값이 곧 "몇 번째 표" 다. */
  private static int[] readSelectors(BitReader r, int nGroups,
      int nSelectors) {
    int[] mtf = new int[nGroups];
    for (int i = 0; i < nGroups; i++) {
      mtf[i] = i;
    }
    int[] out = new int[nSelectors];
    for (int i = 0; i < nSelectors; i++) {
      int j = 0;
      while (r.readBit() != 0) {
        if (++j >= nGroups) {
          throw new CodecException("선택자가 표 개수를 넘는다");
        }
      }
      int v = mtf[j];
      System.arraycopy(mtf, 0, mtf, 1, j);
      mtf[0] = v;
      out[i] = v;
    }
    return out;
  }

  private static Huffman.Decoder[] readTables(BitReader r, int nGroups,
      int alphaSize) {
    Huffman.Decoder[] tables = new Huffman.Decoder[nGroups];
    for (int g = 0; g < nGroups; g++) {
      int length = (int) r.readBits(5);
      int[] lengths = new int[alphaSize];
      for (int s = 0; s < alphaSize; s++) {
        for (;;) {
          if (length < 1 || length > MAX_CODE_LEN) {
            throw CodecException.of("부호 길이가 범위 밖이다: %d",
                length);
          }
          if (r.readBit() == 0) {
            break;
          }
          length += r.readBit() != 0 ? -1 : 1;
        }
        lengths[s] = length;
      }
      Huffman.checkComplete(lengths, MAX_CODE_LEN);
      tables[g] = new Huffman.Decoder(lengths, MAX_CODE_LEN);
    }
    return tables;
  }

  /** 허프만 → MTF 지표 열. RUNA/RUNB 는 여기서 0 의 런으로 편다. */
  private static int[] readBlockSymbols(BitReader r,
      Huffman.Decoder[] tables, int[] selectors, int alphaSize,
      int limit) {
    int eob = alphaSize - 1;
    List<Integer> out = new ArrayList<>();
    int group = 0;
    int left = 0;
    Huffman.Decoder dec = null;
    long run = 0;
    long weight = 1;
    for (;;) {
      if (left == 0) {
        if (group >= selectors.length) {
          throw new CodecException("선택자가 모자란다");
        }
        dec = tables[selectors[group]];
        group++;
        left = GROUP_SIZE;
      }
      left--;
      int sym = dec.read(r);
      if (sym <= RUN_B) {
        run += (long) (sym + 1) * weight;
        weight <<= 1;
        if (run > limit) {
          throw new CodecException("0 런이 블록 크기를 넘는다");
        }
        continue;
      }
      if (run > 0) {
        for (long k = 0; k < run; k++) {
          out.add(0);
        }
        run = 0;
        weight = 1;
      }
      if (sym == eob) {
        return out.stream().mapToInt(Integer::intValue).toArray();
      }
      out.add(sym - 1);
      if (out.size() > limit) {
        throw new CodecException("블록이 상한을 넘는다");
      }
    }
  }

  /** 쓰인 값만 놓고 MTF 를 되돌린다 — 기호 지도가 여기서 값을 한다. */
  private static byte[] inverseMtf(int[] indices, int[] used) {
    int[] table = used.clone();
    byte[] out = new byte[indices.length];
    for (int k = 0; k < indices.length; k++) {
      int i = indices[k];
      if (i >= table.length) {
        throw new CodecException("MTF 지표가 알파벳을 넘는다");
      }
      int v = table[i];
      out[k] = (byte) v;
      if (i != 0) {
        System.arraycopy(table, 0, table, 1, i);
        table[0] = v;
      }
    }
    return out;
  }

  public static byte[] decode(byte[] src) {
    if (src.length < 4 || src[0] != 'B' || src[1] != 'Z'
        || src[2] != 'h') {
      throw new CodecException("bzip2 매직이 아니다");
    }
    int level = (src[3] & 0xFF) - 0x30;
    if (level < 1 || level > 9) {
      throw CodecException.of("블록 크기 등급이 1~9 가 아니다: %d",
          level);
    }
    int limit = level * 100000;
    BitReader r = new BitReader(src, 4);
    ByteBuf out = new ByteBuf();
    int combined = 0;
    for (;;) {
      long magic = r.readBits(48);
      if (magic == END_MAGIC) {
        int want = (int) r.readBits(32);
        if (want != combined) {
          throw new CodecException("합친 CRC 가 다르다");
        }
        return out.bytes();
      }
      if (magic != BLOCK_MAGIC) {
        throw new CodecException("블록 매직이 아니다");
      }
      int blockCrc = (int) r.readBits(32);
      if (r.readBit() != 0) {
        throw new CodecException("무작위화된 블록은 지원하지 않는다");
      }
      int origPtr = (int) r.readBits(24);
      int[] used = readSymbolMap(r);
      int alphaSize = used.length + 2;
      int nGroups = (int) r.readBits(3);
      if (nGroups < 2 || nGroups > MAX_GROUPS) {
        throw CodecException.of("표 개수가 2~6 이 아니다: %d", nGroups);
      }
      int nSelectors = (int) r.readBits(15);
      int[] selectors = readSelectors(r, nGroups, nSelectors);
      Huffman.Decoder[] tables = readTables(r, nGroups, alphaSize);
      int[] indices =
          readBlockSymbols(r, tables, selectors, alphaSize, limit);
      byte[] lColumn = inverseMtf(indices, used);
      if (origPtr >= lColumn.length) {
        throw new CodecException("origPtr 가 블록 밖이다");
      }
      byte[] block = rle1Decode(Bwt.inverseBlock(lColumn, origPtr));
      if (crc32Bzip2(block) != blockCrc) {
        throw new CodecException("블록 CRC 가 다르다");
      }
      combined = ((combined << 1) | (combined >>> 31)) ^ blockCrc;
      out.extend(block);
    }
  }
}
