package compresslib;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * PPM — 부분 일치 예측 — SPEC §17.
 *
 * <p>앞 두 바이트로 다음 바이트를 찍는다. 틀리면 "틀렸다"(탈출) 고
 * 말하고 앞 한 바이트로, 또 틀리면 맨손으로 찍는다. 탈출값은 방법 C 다
 * — — 문맥에서 본 서로 다른 기호의 수가 곧 탈출의 빈도다.
 *
 * <p><b>모두 배제된 문맥은 건너뛴다.</b> 탈출이 확실해 비트가 0이다.
 * 이걸 잊으면 부호기만 탈출을 적어 그 자리에서 어긋난다 — 고전 버그다.
 */
public final class Ppm {
  public static final int MAX_ORDER = 2;
  public static final int ALPHABET = 256;
  /** 문맥의 합계가 이 값에 닿으면 모든 셈을 반으로 줄인다. */
  public static final int MAX_TOTAL = 8192;

  private Ppm() {}

  /** 기호 → 셈. TreeMap 이라 훑는 순서가 늘 번호 오름차순이다. */
  private static final class Table extends TreeMap<Integer, Integer> {
    private static final long serialVersionUID = 1L;
  }

  /** 문맥 열쇠. 길이를 앞에 붙여 ()·(a)·(a,b) 를 구별한다. */
  static String contextKey(List<Integer> history, int order) {
    StringBuilder sb = new StringBuilder();
    sb.append(order);
    for (int i = history.size() - order; i < history.size(); i++) {
      sb.append(',').append(history.get(i));
    }
    return sb.toString();
  }

  static List<String> contextKeys(List<Integer> history) {
    List<String> keys = new ArrayList<>();
    for (int order = MAX_ORDER; order >= 0; order--) {
      if (order > history.size()) {
        continue;
      }
      keys.add(contextKey(history, order));
    }
    return keys;
  }

  private static void update(Map<String, Table> model, String key,
      int sym) {
    Table table = model.computeIfAbsent(key, k -> new Table());
    table.merge(sym, 1, Integer::sum);
    int total = 0;
    for (int v : table.values()) {
      total += v;
    }
    if (total >= MAX_TOTAL) {
      for (Map.Entry<Integer, Integer> e : table.entrySet()) {
        e.setValue(Math.max(1, e.getValue() >> 1));
      }
    }
  }

  /** 배제 안 된 기호를 번호 오름차순으로. 누적합의 순서가 이것이다. */
  private static List<Integer> visible(Table table,
      boolean[] excluded) {
    List<Integer> syms = new ArrayList<>();
    for (int s : table.keySet()) {
      if (!excluded[s]) {
        syms.add(s);
      }
    }
    return syms;
  }

  private static void pushHistory(List<Integer> history, int b) {
    history.add(b);
    if (history.size() > MAX_ORDER) {
      history.remove(0);
    }
  }

  public static byte[] encode(byte[] src) {
    if (src.length == 0) {
      return Varint.put(0);
    }
    RangeCoder.Encoder enc = new RangeCoder.Encoder();
    Map<String, Table> model = new HashMap<>();
    List<Integer> history = new ArrayList<>();
    for (byte raw : src) {
      int b = raw & 0xFF;
      boolean[] excluded = new boolean[ALPHABET];
      boolean coded = false;
      for (String key : contextKeys(history)) {
        Table table = model.get(key);
        if (table == null) {
          continue;
        }
        List<Integer> syms = visible(table, excluded);
        if (syms.isEmpty()) {
          continue;       // 모두 배제 — 아무것도 안 적는다
        }
        long esc = syms.size();
        long tot = esc;
        for (int s : syms) {
          tot += table.get(s);
        }
        if (!excluded[b] && table.containsKey(b)) {
          long cum = 0;
          for (int s : syms) {
            if (s == b) {
              break;
            }
            cum += table.get(s);
          }
          enc.encodeFreq(cum, table.get(b), tot);
          coded = true;
          break;
        }
        enc.encodeFreq(tot - esc, esc, tot);
        for (int s : syms) {
          excluded[s] = true;
        }
      }
      if (!coded) {
        // -1차 — 남은 기호에 균등하게 (§17.4)
        long rest = 0;
        long index = 0;
        for (int s = 0; s < ALPHABET; s++) {
          if (excluded[s]) {
            continue;
          }
          if (s < b) {
            index++;
          }
          rest++;
        }
        enc.encodeFreq(index, 1, rest);
      }
      for (String key : contextKeys(history)) {
        update(model, key, b);
      }
      pushHistory(history, b);
    }
    enc.flush();
    ByteBuf out = new ByteBuf();
    Varint.put(out, src.length);
    out.extend(enc.bytes());
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
    RangeCoder.Decoder dec = new RangeCoder.Decoder(src, h[1]);
    Map<String, Table> model = new HashMap<>();
    List<Integer> history = new ArrayList<>();
    byte[] out = new byte[n];
    for (int k = 0; k < n; k++) {
      boolean[] excluded = new boolean[ALPHABET];
      int found = -1;
      for (String key : contextKeys(history)) {
        Table table = model.get(key);
        if (table == null) {
          continue;
        }
        List<Integer> syms = visible(table, excluded);
        if (syms.isEmpty()) {
          continue;
        }
        long esc = syms.size();
        long tot = esc;
        for (int s : syms) {
          tot += table.get(s);
        }
        long v = dec.decodeFreq(tot);
        long cum = 0;
        int hit = -1;
        for (int s : syms) {
          int c = table.get(s);
          if (v >= cum && v < cum + c) {
            hit = s;
            break;
          }
          cum += c;
        }
        if (hit >= 0) {
          dec.decodeUpdate(cum, table.get(hit), tot);
          found = hit;
          break;
        }
        dec.decodeUpdate(tot - esc, esc, tot);
        for (int s : syms) {
          excluded[s] = true;
        }
      }
      if (found < 0) {
        List<Integer> rest = new ArrayList<>();
        for (int s = 0; s < ALPHABET; s++) {
          if (!excluded[s]) {
            rest.add(s);
          }
        }
        long v = dec.decodeFreq(rest.size());
        found = rest.get((int) v);
        dec.decodeUpdate(v, 1, rest.size());
      }
      out[k] = (byte) found;
      for (String key : contextKeys(history)) {
        update(model, key, found);
      }
      pushHistory(history, found);
    }
    return out;
  }
}
