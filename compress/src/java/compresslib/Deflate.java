package compresslib;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * DEFLATE 부호기 — SPEC §10.
 *
 * <p>RFC 가 부호기에 맡긴 선택을 전부 못 박은 것이 이 파일이다. 블록
 * 65535, 값을 정확히 세어 가장 작은 것, 같으면 stored → fixed →
 * dynamic. 값을 어림하면 언어마다 반올림이 달라져 블록 종류가 갈린다.
 */
public final class Deflate {
  public static final int BLOCK_SIZE = 65535;
  public static final int HASH_BITS = 15;
  public static final int HASH_SIZE = 1 << HASH_BITS;
  public static final int CHAIN_LIMIT = 128;
  static final int NIL = -1;

  private Deflate() {}

  private static final class ClItem {
    final int sym;
    final int value;
    final int nbits;

    ClItem(int sym, int value, int nbits) {
      this.sym = sym;
      this.value = value;
      this.nbits = nbits;
    }
  }

  static int hash3(byte[] s, int i) {
    int h = ((s[i] & 0xFF) << 10) ^ ((s[i + 1] & 0xFF) << 5)
        ^ (s[i + 2] & 0xFF);
    return h & (HASH_SIZE - 1);
  }

  public static List<Lzss.Token> parse(byte[] src) {
    int n = src.length;
    int[] head = new int[HASH_SIZE];
    Arrays.fill(head, NIL);
    int[] prev = new int[Math.max(n, 1)];
    Arrays.fill(prev, NIL);
    List<Lzss.Token> tokens = new ArrayList<>();
    int[] best = new int[2];      // {길이, 거리}
    int i = 0;
    while (i < n) {
      find(src, i, head, prev, best);
      int ln = best[0];
      int dist = best[1];
      insert(src, i, head, prev);
      if (ln >= DeflateTables.MIN_MATCH) {
        int nxtLen = 0;
        if (i + 1 < n) {
          find(src, i + 1, head, prev, best);
          nxtLen = best[0];
        }
        if (nxtLen > ln) {      // 게으른 일치
          tokens.add(new Lzss.Token(false, src[i] & 0xFF, 0, 0));
          i++;
          continue;
        }
        for (int k = 1; k < ln; k++) {
          insert(src, i + k, head, prev);
        }
        tokens.add(new Lzss.Token(true, 0, ln, dist));
        i += ln;
      } else {
        tokens.add(new Lzss.Token(false, src[i] & 0xFF, 0, 0));
        i++;
      }
    }
    return tokens;
  }

  private static void insert(byte[] src, int p, int[] head,
      int[] prev) {
    if (p + DeflateTables.MIN_MATCH <= src.length) {
      int h = hash3(src, p);
      prev[p] = head[h];
      head[h] = p;
    }
  }

  private static void find(byte[] src, int p, int[] head, int[] prev,
      int[] out) {
    out[0] = 0;
    out[1] = 0;
    int n = src.length;
    if (p + DeflateTables.MIN_MATCH > n) {
      return;
    }
    int limit = Math.min(DeflateTables.MAX_MATCH, n - p);
    int cand = head[hash3(src, p)];
    int probes = 0;
    while (cand != NIL && probes < CHAIN_LIMIT) {
      int dist = p - cand;
      if (dist > DeflateTables.MAX_DIST) {
        break;
      }
      int ln = 0;
      while (ln < limit && src[cand + ln] == src[p + ln]) {
        ln++;
      }
      if (ln > out[0]) {
        out[0] = ln;
        out[1] = dist;
        if (ln == limit) {
          break;
        }
      }
      cand = prev[cand];
      probes++;
    }
  }

  private static final class Block {
    final int tokA;
    final int tokB;
    final int inA;
    final int inB;

    Block(int tokA, int tokB, int inA, int inB) {
      this.tokA = tokA;
      this.tokB = tokB;
      this.inA = inA;
      this.inB = inB;
    }
  }

  private static List<Block> splitBlocks(List<Lzss.Token> tokens) {
    List<Block> blocks = new ArrayList<>();
    int tokStart = 0;
    int inStart = 0;
    int cur = 0;
    for (int k = 0; k < tokens.size(); k++) {
      Lzss.Token t = tokens.get(k);
      cur += t.isMatch ? t.length : 1;
      if (cur >= BLOCK_SIZE) {
        blocks.add(new Block(tokStart, k + 1, inStart, inStart + cur));
        tokStart = k + 1;
        inStart += cur;
        cur = 0;
      }
    }
    if (cur > 0 || blocks.isEmpty()) {
      blocks.add(
          new Block(tokStart, tokens.size(), inStart, inStart + cur));
    }
    return blocks;
  }

  /** 빈도를 세고 여분 비트 수를 돌려준다. */
  private static int freqsOf(List<Lzss.Token> tokens, int a, int b,
      long[] lit, long[] dst) {
    Arrays.fill(lit, 0);
    Arrays.fill(dst, 0);
    int extra = 0;
    for (int k = a; k < b; k++) {
      Lzss.Token t = tokens.get(k);
      if (t.isMatch) {
        int code = DeflateTables.LENGTH_CODE[t.length];
        lit[code]++;
        extra += DeflateTables.LENGTH_EXTRA[code - 257];
        int dc = DeflateTables.distCode(t.dist);
        dst[dc]++;
        extra += DeflateTables.DIST_EXTRA[dc];
      } else {
        lit[t.literal]++;
      }
    }
    lit[DeflateTables.END_OF_BLOCK]++;
    return extra;
  }

  private static long bodyBits(long[] lit, long[] dst, int extra,
      int[] litLen, int[] dstLen) {
    long bits = extra;
    for (int s = 0; s < lit.length; s++) {
      if (lit[s] > 0) {
        bits += lit[s] * litLen[s];
      }
    }
    for (int s = 0; s < dst.length; s++) {
      if (dst[s] > 0) {
        bits += dst[s] * dstLen[s];
      }
    }
    return bits;
  }

  /** 부호 길이 배열 → (기호, 여분 값, 여분 비트). 왼쪽부터 탐욕. */
  private static List<ClItem> clEncode(int[] lengths) {
    List<ClItem> out = new ArrayList<>();
    int i = 0;
    int n = lengths.length;
    while (i < n) {
      int cur = lengths[i];
      int run = 1;
      while (i + run < n && lengths[i + run] == cur) {
        run++;
      }
      if (cur == 0) {
        while (run >= 3) {
          int k;
          if (run >= 11) {
            k = Math.min(run, 138);
            out.add(new ClItem(DeflateTables.CL_ZERO_LONG, k - 11, 7));
          } else {
            k = Math.min(run, 10);
            out.add(new ClItem(DeflateTables.CL_ZERO_SHORT, k - 3, 3));
          }
          run -= k;
          i += k;
        }
        for (int j = 0; j < run; j++) {
          out.add(new ClItem(0, 0, 0));
          i++;
        }
      } else {
        out.add(new ClItem(cur, 0, 0));
        i++;
        run--;
        while (run >= 3) {
          int k = Math.min(run, 6);
          out.add(new ClItem(DeflateTables.CL_REPEAT, k - 3, 2));
          run -= k;
          i += k;
        }
        for (int j = 0; j < run; j++) {
          out.add(new ClItem(cur, 0, 0));
          i++;
        }
      }
    }
    return out;
  }

  private static int lastUsed(int[] lengths) {
    for (int s = lengths.length; s > 0; s--) {
      if (lengths[s - 1] > 0) {
        return s;
      }
    }
    return 0;
  }

  private static final class DynamicPlan {
    final int[] litLen;
    final int[] dstLen;
    final int[] clLen;
    final List<ClItem> items;
    final int hlit;
    final int hdist;
    int hclen;
    final long bits;

    DynamicPlan(long[] litFreq, long[] dstFreq, int extra) {
      litLen = Huffman.codeLengths(litFreq, Huffman.MAX_LENGTH);
      dstLen = Huffman.codeLengths(dstFreq, Huffman.MAX_LENGTH);
      boolean any = false;
      for (int l : dstLen) {
        any = any || l > 0;
      }
      if (!any) {
        // 일치가 하나도 없는 블록. 거리 부호를 안 보낼 수는 없으므로
        // 하나를 길이 1 로 보낸다 — 쓰이지 않는 부호다 (§10.5).
        dstLen[0] = 1;
      }
      hlit = Math.max(257, lastUsed(litLen));
      hdist = Math.max(1, lastUsed(dstLen));
      int[] joined = new int[hlit + hdist];
      System.arraycopy(litLen, 0, joined, 0, hlit);
      System.arraycopy(dstLen, 0, joined, hlit, hdist);
      items = clEncode(joined);
      long[] clFreq = new long[DeflateTables.CL_SYMBOLS];
      for (ClItem it : items) {
        clFreq[it.sym]++;
      }
      clLen = Huffman.codeLengths(clFreq, DeflateTables.CL_MAX_LENGTH);
      hclen = DeflateTables.CL_SYMBOLS;
      while (hclen > 4
          && clLen[DeflateTables.CL_ORDER[hclen - 1]] == 0) {
        hclen--;
      }
      long header = 5 + 5 + 4 + 3L * hclen;
      for (ClItem it : items) {
        header += clLen[it.sym] + it.nbits;
      }
      bits = 3 + header
          + bodyBits(litFreq, dstFreq, extra, litLen, dstLen);
    }
  }

  private static void writeBody(BitIO.LsbWriter w,
      List<Lzss.Token> tokens, int a, int b, int[] litLen,
      int[] litCode, int[] dstLen, int[] dstCode) {
    for (int k = a; k < b; k++) {
      Lzss.Token t = tokens.get(k);
      if (t.isMatch) {
        int code = DeflateTables.LENGTH_CODE[t.length];
        w.writeCode(litCode[code], litLen[code]);
        int idx = code - 257;
        if (DeflateTables.LENGTH_EXTRA[idx] > 0) {
          w.writeBits(t.length - DeflateTables.LENGTH_BASE[idx],
              DeflateTables.LENGTH_EXTRA[idx]);
        }
        int dc = DeflateTables.distCode(t.dist);
        w.writeCode(dstCode[dc], dstLen[dc]);
        if (DeflateTables.DIST_EXTRA[dc] > 0) {
          w.writeBits(t.dist - DeflateTables.DIST_BASE[dc],
              DeflateTables.DIST_EXTRA[dc]);
        }
      } else {
        w.writeCode(litCode[t.literal], litLen[t.literal]);
      }
    }
    int eob = DeflateTables.END_OF_BLOCK;
    w.writeCode(litCode[eob], litLen[eob]);
  }

  public static byte[] deflateRaw(byte[] src) {
    BitIO.LsbWriter w = new BitIO.LsbWriter();
    if (src.length == 0) {
      // 마지막 고정 블록 하나, 안에는 블록 끝 기호뿐. 두 바이트 03 00.
      w.writeBits(1, 1);
      w.writeBits(1, 2);
      w.writeCode(0, 7);
      w.flush();
      return w.bytes();
    }
    List<Lzss.Token> tokens = parse(src);
    List<Block> blocks = splitBlocks(tokens);
    int[] fixedCode =
        Huffman.canonicalCodes(DeflateTables.FIXED_LITLEN);
    int[] fixedDcode = Huffman.canonicalCodes(DeflateTables.FIXED_DIST);
    long[] litFreq = new long[DeflateTables.LITLEN_SYMBOLS];
    long[] dstFreq = new long[DeflateTables.DIST_SYMBOLS];
    for (int k = 0; k < blocks.size(); k++) {
      Block blk = blocks.get(k);
      int last = (k == blocks.size() - 1) ? 1 : 0;
      int extra = freqsOf(tokens, blk.tokA, blk.tokB, litFreq, dstFreq);
      int rawLen = blk.inB - blk.inA;
      // stored 의 값은 지금 비트 자리에 달려 있다 — 정렬 때문이다.
      int pad = (8 - ((w.bitPos() + 3) % 8)) % 8;
      long costStored = 3L + pad + 32 + 8L * rawLen;
      long costFixed = 3 + bodyBits(litFreq, dstFreq, extra,
          DeflateTables.FIXED_LITLEN, DeflateTables.FIXED_DIST);
      DynamicPlan plan = new DynamicPlan(litFreq, dstFreq, extra);
      if (costStored <= costFixed && costStored <= plan.bits) {
        w.writeBits(last, 1);
        w.writeBits(0, 2);
        w.align();
        w.writeBits(rawLen, 16);
        w.writeBits(rawLen ^ 0xFFFF, 16);
        for (int j = blk.inA; j < blk.inB; j++) {
          w.writeBits(src[j] & 0xFF, 8);
        }
        continue;
      }
      w.writeBits(last, 1);
      if (costFixed <= plan.bits) {
        w.writeBits(1, 2);
        writeBody(w, tokens, blk.tokA, blk.tokB,
            DeflateTables.FIXED_LITLEN, fixedCode,
            DeflateTables.FIXED_DIST, fixedDcode);
        continue;
      }
      w.writeBits(2, 2);
      w.writeBits(plan.hlit - 257, 5);
      w.writeBits(plan.hdist - 1, 5);
      w.writeBits(plan.hclen - 4, 4);
      for (int i = 0; i < plan.hclen; i++) {
        w.writeBits(plan.clLen[DeflateTables.CL_ORDER[i]], 3);
      }
      int[] clCode = Huffman.canonicalCodes(plan.clLen);
      for (ClItem it : plan.items) {
        w.writeCode(clCode[it.sym], plan.clLen[it.sym]);
        if (it.nbits > 0) {
          w.writeBits(it.value, it.nbits);
        }
      }
      writeBody(w, tokens, blk.tokA, blk.tokB, plan.litLen,
          Huffman.canonicalCodes(plan.litLen), plan.dstLen,
          Huffman.canonicalCodes(plan.dstLen));
    }
    w.flush();
    return w.bytes();
  }

  // 골든 코덱. 다른 모듈과 달리 varint 헤더가 없다 — 남의 형식이라
  // 우리가 얹을 자리가 없고, 원본 길이는 스트림 자신이 알고 있다.
  public static byte[] encode(byte[] src) {
    return deflateRaw(src);
  }

  public static byte[] decode(byte[] src) {
    return Inflate.inflateRaw(src);
  }
}
