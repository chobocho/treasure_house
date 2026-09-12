package compresslib;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * LZ77 계열 — SPEC §6.
 *
 * <p>사슬 배열을 <b>절대 위치로</b> 잡는다. zlib 은 창 크기 배열에 감아
 * 넣어서 pos-32768 자리를 pos 가 덮어쓰고, 그래서 실효 최대 거리가
 * 32506 이다. 후보 교체 비교는 &gt; 다. &gt;= 로 쓰면 같은 길이에서 먼
 * 쪽을 골라, 정상 복호되는 <b>다른</b> 파일이 나온다.
 */
public final class Lzss {
  public static final int WINDOW = 32768;
  public static final int MIN_MATCH = 3;
  public static final int MAX_MATCH = 258;
  public static final int HASH_BITS = 15;
  public static final int HASH_SIZE = 1 << HASH_BITS;
  public static final int CHAIN_LIMIT = 32;
  static final int NIL = -1;

  private Lzss() {}

  /** 리터럴이거나 (길이, 거리). isMatch 가 거짓이면 literal 만 쓴다. */
  public static final class Token {
    public final boolean isMatch;
    public final int literal;
    public final int length;
    public final int dist;

    Token(boolean isMatch, int literal, int length, int dist) {
      this.isMatch = isMatch;
      this.literal = literal;
      this.length = length;
      this.dist = dist;
    }
  }

  static int hash3(byte[] s, int i) {
    int h = ((s[i] & 0xFF) << 10) ^ ((s[i + 1] & 0xFF) << 5)
        ^ (s[i + 2] & 0xFF);
    return h & (HASH_SIZE - 1);
  }

  public static List<Token> findTokens(byte[] src) {
    int n = src.length;
    int[] head = new int[HASH_SIZE];
    Arrays.fill(head, NIL);
    int[] prev = new int[Math.max(n, 1)];
    Arrays.fill(prev, NIL);
    List<Token> tokens = new ArrayList<>();
    int i = 0;
    while (i < n) {
      int bestLen = 0;
      int bestDist = 0;
      if (i + MIN_MATCH <= n) {
        int limit = Math.min(MAX_MATCH, n - i);
        int cand = head[hash3(src, i)];
        int probes = 0;
        while (cand != NIL && probes < CHAIN_LIMIT) {
          int dist = i - cand;
          if (dist > WINDOW) {
            break;
          }
          int ln = 0;
          while (ln < limit && src[cand + ln] == src[i + ln]) {
            ln++;
          }
          if (ln > bestLen) {
            bestLen = ln;
            bestDist = dist;
            if (ln == limit) {
              break;
            }
          }
          cand = prev[cand];
          probes++;
        }
      }
      if (bestLen >= MIN_MATCH) {
        for (int k = 0; k < bestLen; k++) {
          int p = i + k;
          if (p + MIN_MATCH <= n) {
            int h = hash3(src, p);
            prev[p] = head[h];
            head[h] = p;
          }
        }
        tokens.add(new Token(true, 0, bestLen, bestDist));
        i += bestLen;
      } else {
        if (i + MIN_MATCH <= n) {
          int h = hash3(src, i);
          prev[i] = head[h];
          head[h] = i;
        }
        tokens.add(new Token(false, src[i] & 0xFF, 0, 0));
        i++;
      }
    }
    return tokens;
  }

  public static byte[] encode(byte[] src) {
    List<Token> tokens = findTokens(src);
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    for (int base = 0; base < tokens.size(); base += 8) {
      int end = Math.min(base + 8, tokens.size());
      int flag = 0;
      for (int k = base; k < end; k++) {
        if (tokens.get(k).isMatch) {
          flag |= 1 << (7 - (k - base));
        }
      }
      out.push(flag);
      for (int k = base; k < end; k++) {
        Token t = tokens.get(k);
        if (t.isMatch) {
          int d = t.dist - 1;
          out.push(t.length - MIN_MATCH);
          out.push(d & 0xFF);
          out.push(d >>> 8);
        } else {
          out.push(t.literal);
        }
      }
    }
    return out.bytes();
  }

  public static byte[] decode(byte[] src) {
    int[] h = Varint.getLength(src, 0);
    int n = h[0];
    int pos = h[1];
    int end = src.length;
    ByteBuf out = new ByteBuf();
    while (out.size() < n) {
      if (pos >= end) {
        throw new CodecException("플래그 바이트가 없다");
      }
      int flag = src[pos++] & 0xFF;
      for (int k = 0; k < 8 && out.size() < n; k++) {
        if ((flag & (1 << (7 - k))) != 0) {
          if (pos + 3 > end) {
            throw new CodecException("일치 토큰이 잘렸다");
          }
          int ln = (src[pos] & 0xFF) + MIN_MATCH;
          int dist = ((src[pos + 1] & 0xFF)
              | ((src[pos + 2] & 0xFF) << 8)) + 1;
          pos += 3;
          if (dist > out.size()) {
            throw CodecException.of("거리 %d 가 낸 것보다 멀다", dist);
          }
          int at = out.size() - dist;
          // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다 —
          // arraycopy 로 한 번에 옮기면 틀린다.
          for (int j = 0; j < ln; j++) {
            out.push(out.at(at + j));
          }
        } else {
          if (pos >= end) {
            throw new CodecException("리터럴이 잘렸다");
          }
          out.push(src[pos++] & 0xFF);
        }
      }
    }
    if (out.size() != n) {
      throw new CodecException("푼 길이가 헤더와 다르다");
    }
    if (pos != end) {
      throw new CodecException("뒤에 남은 바이트가 있다");
    }
    return out.bytes();
  }
}
