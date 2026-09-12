package compresslib;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * inflate — RFC 1951 복호기 (SPEC §10.7).
 *
 * <p>부호기보다 복호기가 먼저다. 형식을 읽을 줄 알아야 내가 쓴 것이
 * 맞는지 알 수 있고, 무엇보다 진짜 gzip 이 만든 파일을 풀 수 있어야
 * 한다.
 *
 * <p>예외 하나: 거리 부호가 하나뿐인 표는 크래프트 합이 1/2 라 "모자란"
 * 표인데, RFC 가 허용하고 zlib 도 낸다. 일치 없는 블록에서 나온다.
 */
public final class Inflate {
  private Inflate() {}

  static Huffman.Decoder table(int[] lengths) {
    Huffman.checkComplete(lengths);
    return new Huffman.Decoder(lengths);
  }

  static void readBody(BitIO.LsbReader r, ByteBuf out,
      Huffman.Decoder litlen, Huffman.Decoder dist) {
    for (;;) {
      int sym = litlen.read(r);
      if (sym < 256) {
        out.push(sym);
        continue;
      }
      if (sym == DeflateTables.END_OF_BLOCK) {
        return;
      }
      int idx = sym - 257;
      if (idx >= DeflateTables.LENGTH_BASE.length) {
        throw CodecException.of("길이 부호 %d 는 없다", sym);
      }
      int length = DeflateTables.LENGTH_BASE[idx]
          + (int) r.readBits(DeflateTables.LENGTH_EXTRA[idx]);
      int dcode = dist.read(r);
      if (dcode >= DeflateTables.DIST_SYMBOLS) {
        throw CodecException.of("거리 부호 %d 는 쓰이지 않는다", dcode);
      }
      int d = DeflateTables.DIST_BASE[dcode]
          + (int) r.readBits(DeflateTables.DIST_EXTRA[dcode]);
      if (d > out.size()) {
        throw CodecException.of("거리 %d 가 낸 것보다 멀다", d);
      }
      int at = out.size() - d;
      // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
      for (int k = 0; k < length; k++) {
        out.push(out.at(at + k));
      }
    }
  }

  static Huffman.Decoder[] readDynamic(BitIO.LsbReader r) {
    int hlit = (int) r.readBits(5) + 257;
    int hdist = (int) r.readBits(5) + 1;
    int hclen = (int) r.readBits(4) + 4;
    if (hlit > DeflateTables.LITLEN_SYMBOLS
        || hdist > DeflateTables.DIST_SYMBOLS) {
      throw new CodecException("HLIT/HDIST 가 알파벳을 넘는다");
    }
    int[] clLengths = new int[DeflateTables.CL_SYMBOLS];
    for (int i = 0; i < hclen; i++) {
      clLengths[DeflateTables.CL_ORDER[i]] = (int) r.readBits(3);
    }
    Huffman.Decoder cl = table(clLengths);

    List<Integer> lengths = new ArrayList<>();
    int want = hlit + hdist;
    while (lengths.size() < want) {
      int sym = cl.read(r);
      if (sym < 16) {
        lengths.add(sym);
      } else if (sym == DeflateTables.CL_REPEAT) {
        if (lengths.isEmpty()) {
          throw new CodecException("부호 16 이 맨 앞에 왔다");
        }
        int prev = lengths.get(lengths.size() - 1);
        for (int i = (int) r.readBits(2) + 3; i > 0; i--) {
          lengths.add(prev);
        }
      } else if (sym == DeflateTables.CL_ZERO_SHORT) {
        for (int i = (int) r.readBits(3) + 3; i > 0; i--) {
          lengths.add(0);
        }
      } else {
        for (int i = (int) r.readBits(7) + 11; i > 0; i--) {
          lengths.add(0);
        }
      }
    }
    if (lengths.size() != want) {
      throw new CodecException("부호 길이 되풀이가 표 끝을 넘었다");
    }
    int[] all = lengths.stream().mapToInt(Integer::intValue).toArray();
    return new Huffman.Decoder[] {
        table(Arrays.copyOfRange(all, 0, hlit)),
        table(Arrays.copyOfRange(all, hlit, all.length))};
  }

  public static byte[] inflateRaw(byte[] src) {
    BitIO.LsbReader r = new BitIO.LsbReader(src, 0);
    ByteBuf out = new ByteBuf();
    Huffman.Decoder fixedLit = null;
    Huffman.Decoder fixedDst = null;
    for (;;) {
      int last = r.readBit();
      int btype = (int) r.readBits(2);
      if (btype == 0) {
        r.align();
        int p = r.pos;
        if (p + 4 > src.length) {
          throw new CodecException("stored 블록 머리가 잘렸다");
        }
        int ln = (src[p] & 0xFF) | ((src[p + 1] & 0xFF) << 8);
        int nln = (src[p + 2] & 0xFF) | ((src[p + 3] & 0xFF) << 8);
        p += 4;
        if (ln != (nln ^ 0xFFFF)) {
          throw new CodecException("NLEN 이 LEN 의 보수가 아니다");
        }
        if (p + ln > src.length) {
          throw new CodecException("stored 블록 몸통이 잘렸다");
        }
        out.extend(src, p, p + ln);
        r.pos = p + ln;
      } else if (btype == 1) {
        if (fixedLit == null) {
          fixedLit = table(DeflateTables.FIXED_LITLEN);
          fixedDst = table(DeflateTables.FIXED_DIST);
        }
        readBody(r, out, fixedLit, fixedDst);
      } else if (btype == 2) {
        Huffman.Decoder[] pair = readDynamic(r);
        readBody(r, out, pair[0], pair[1]);
      } else {
        throw new CodecException("BTYPE 11 은 없는 블록 종류다");
      }
      if (last != 0) {
        return out.bytes();
      }
    }
  }
}
