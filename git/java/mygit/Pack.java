package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.Function;
import java.util.zip.CRC32;

// 팩 (SPEC.md §13) — 객체 여럿을 한 파일에, 비슷한 것은 델타로.
//
// 느슨한 객체는 파일 하나에 객체 하나지만, 팩은 객체들을 이어 붙이고
// 비슷한 객체는 "바탕에서 여기를 복사, 여기에 이것을 끼움" 이라는
// 델타로 적는다. 색인(.idx)은 이름 → 팩 안 자리의 표다. 팩 끝
// 20바이트는 팩 전체의 SHA-1 이고, 그것이 곧 파일 이름이다.
public final class Pack {
  private static final List<String> TYPE_NAMES =
      List.of("", "commit", "tree", "blob", "tag");
  static final int OFS_DELTA = 6;
  static final int REF_DELTA = 7;
  private static final int BLOCK = 16;
  private static final HexFormat HEX = HexFormat.of();

  private Pack() {}

  // 팩 항목 하나를 되살린 것. packedType 은 팩에 적힌 형식(6·7 은
  // 델타), type·body 는 되살린 객체, depth·base 는 델타 사슬.
  public static final class PackEntry {
    public long offset;
    public long end;
    public long crc;
    public int packedType;
    public byte[] delta;
    public long baseOffset = -1;
    public String base;
    public String type;
    public byte[] body;
    public String oid;
    public int depth;
  }

  // 색인의 한 줄과 색인 전체
  public record IdxEntry(String oid, long offset, long crc) {}

  public record Idx(List<IdxEntry> entries, byte[] packSum) {}

  // 팩 바이트를 앞에서부터 읽는 자 — 읽은 만큼 pos 가 간다
  private static final class Reader {
    final byte[] data;
    int pos;

    Reader(byte[] data, int pos) {
      this.data = data;
      this.pos = pos;
    }

    int next() {
      return data[pos++] & 0xff;
    }

    // 7비트씩 작은 쪽부터(델타 머리의 크기)
    long varintLE() {
      long val = 0;
      for (int shift = 0;; shift += 7) {
        int b = next();
        val |= (long) (b & 0x7f) << shift;
        if ((b & 0x80) == 0) return val;
      }
    }

    // OFS_DELTA 의 거리 — 큰 쪽부터, 이어지는 바이트마다 +1
    long ofs() {
      int b = next();
      long n = b & 0x7f;
      while ((b & 0x80) != 0) {
        b = next();
        n = ((n + 1) << 7) | (b & 0x7f);
      }
      return n;
    }
  }

  private static long crc(byte[] data, long from, long to) {
    CRC32 c = new CRC32();
    c.update(data, (int) from, (int) (to - from));
    return c.getValue();
  }

  private static byte[] sha1Of(byte[] data, int len) {
    return new Sha1().update(data, 0, len).digest();
  }

  private static boolean trailerOk(byte[] data) {
    int n = data.length;
    return Arrays.equals(sha1Of(data, n - 20),
        Arrays.copyOfRange(data, n - 20, n));
  }

  // 델타를 바탕에 적용한다(SPEC.md §13.1). O(결과 길이).
  public static byte[] applyDelta(byte[] base, byte[] delta) {
    Reader r = new Reader(delta, 0);
    if (r.varintLE() != base.length) {
      throw new GitError("fatal: mygit: delta base size mismatch");
    }
    long want = r.varintLE();
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    while (r.pos < delta.length) {
      int op = r.next();
      if ((op & 0x80) != 0) {                        // 복사
        long off = 0;
        int n = 0;
        for (int k = 0; k < 4; k++) {
          if ((op & (1 << k)) != 0) off |= (long) r.next() << (8 * k);
        }
        for (int k = 0; k < 3; k++) {
          if ((op & (0x10 << k)) != 0) n |= r.next() << (8 * k);
        }
        n = n == 0 ? 0x10000 : n;
        if (off + n > base.length) {
          throw new GitError("fatal: mygit: delta copy out of range");
        }
        out.write(base, (int) off, n);
      } else if (op != 0) {                          // 끼움
        out.write(delta, r.pos, op);
        r.pos += op;
      } else {
        throw new GitError("fatal: mygit: delta opcode 0 is reserved");
      }
    }
    if (out.size() != want) {
      throw new GitError("fatal: mygit: delta result size mismatch");
    }
    return out.toByteArray();
  }

  // 팩 바이트 → 항목들, 자리 차례. external(이름) 은 팩 밖의
  // REF_DELTA 바탕을 준다(null 이면 팩 안에서만 찾는다).
  //
  // 앞에서부터 읽으며 zlib 스트림이 먹은 바이트 수로 다음 항목을
  // 찾고, 델타는 바탕을 먼저 되살린 뒤 적용한다.
  // O(팩 크기 + 되살린 크기).
  public static List<PackEntry> readPack(byte[] data,
      Function<String, Objects.Obj> external) {
    if (data.length < 32
        || !new String(data, 0, 4, ISO_8859_1).equals("PACK")) {
      throw new GitError("fatal: mygit: not a pack file");
    }
    if (!trailerOk(data)) {
      throw new GitError("fatal: mygit: pack checksum mismatch");
    }
    ByteBuffer bb = ByteBuffer.wrap(data);
    int ver = bb.getInt(4);
    if (ver != 2 && ver != 3) {
      throw new GitError("fatal: mygit: pack version " + ver);
    }
    List<PackEntry> ents = new ArrayList<>();
    Reader r = new Reader(data, 12);
    for (int k = bb.getInt(8); k > 0; k--) {
      PackEntry e = new PackEntry();
      e.offset = r.pos;
      // 항목 머리 — 첫 바이트의 비트 6‥4 가 형식, 낮은 4비트가 크기의
      // 시작이고, 이어지는 바이트는 7비트씩 위로 붙는다
      int b = r.next();
      e.packedType = (b >> 4) & 7;
      long size = b & 15;
      for (int shift = 4; (b & 0x80) != 0; shift += 7) {
        b = r.next();
        size |= (long) (b & 0x7f) << shift;
      }
      if (e.packedType == OFS_DELTA) {
        e.baseOffset = e.offset - r.ofs();
      } else if (e.packedType == REF_DELTA) {
        e.base = HEX.formatHex(data, r.pos, r.pos + 20);
        r.pos += 20;
      } else if (e.packedType < 1 || e.packedType > 4) {
        throw new GitError("fatal: mygit: bad pack entry type "
            + e.packedType);
      }
      Zlib.Inflated z = Zlib.decompressPrefix(data, r.pos);
      if (z.data().length != size) {
        throw new GitError("fatal: mygit: pack entry size mismatch");
      }
      r.pos += z.used();
      e.end = r.pos;
      e.crc = crc(data, e.offset, e.end);
      if (e.packedType <= 4) {
        e.type = TYPE_NAMES.get(e.packedType);
        e.body = z.data();
      } else {
        e.delta = z.data();
      }
      ents.add(e);
    }
    if (r.pos != data.length - 20) {
      throw new GitError("fatal: mygit: pack has trailing garbage");
    }
    resolve(ents, external);
    return ents;
  }

  // 델타 사슬을 풀어 형식·몸·이름·깊이를 채운다. 바탕이 아직 안 풀린
  // 델타는 다음 바퀴로 미룬다 — 바퀴마다 적어도 하나는 풀려야 한다.
  private static void resolve(List<PackEntry> ents,
      Function<String, Objects.Obj> external) {
    Map<Long, PackEntry> byOff = new HashMap<>();
    Map<String, PackEntry> byOid = new HashMap<>();
    List<PackEntry> pending = new ArrayList<>();
    for (PackEntry e : ents) {
      byOff.put(e.offset, e);
      if (e.body == null) {
        pending.add(e);
        continue;
      }
      e.oid = Objects.hashObject(e.type, e.body);
      byOid.put(e.oid, e);
    }
    while (!pending.isEmpty()) {
      List<PackEntry> left = new ArrayList<>();
      for (PackEntry e : pending) {
        PackEntry b;
        if (e.baseOffset >= 0) {
          b = byOff.get(e.baseOffset);
          if (b == null) {
            throw new GitError("fatal: mygit: bad OFS_DELTA base");
          }
        } else {
          b = byOid.get(e.base);
          if (b == null && external != null) {
            Objects.Obj o = external.apply(e.base);
            e.type = o.type();
            e.body = applyDelta(o.body(), e.delta);
            e.depth = 1;
            e.oid = Objects.hashObject(e.type, e.body);
            byOid.put(e.oid, e);
            continue;
          }
        }
        if (b == null || b.body == null) {
          left.add(e);
          continue;
        }
        e.type = b.type;
        e.body = applyDelta(b.body, e.delta);
        e.depth = b.depth + 1;
        e.base = b.oid;
        e.oid = Objects.hashObject(e.type, e.body);
        byOid.put(e.oid, e);
      }
      if (left.size() == pending.size()) {
        throw new GitError("fatal: mygit: unresolved delta base");
      }
      pending = left;
    }
  }

  // 색인 판 2 → 항목들과 팩 체크섬.
  public static Idx readIdx(byte[] data) {
    if (data.length < 1072 || !HEX.formatHex(data, 0, 8)
        .equals("ff744f6300000002")) {
      throw new GitError("fatal: mygit: not a version 2 pack index");
    }
    if (!trailerOk(data)) {
      throw new GitError("fatal: mygit: pack index checksum mismatch");
    }
    ByteBuffer b = ByteBuffer.wrap(data);
    int n = b.getInt(8 + 255 * 4);
    int names = 8 + 256 * 4;
    int crcs = names + 20 * n;
    int small = crcs + 4 * n;
    int big = small + 4 * n;
    List<IdxEntry> out = new ArrayList<>();
    for (int k = 0; k < n; k++) {
      long off = b.getInt(small + 4 * k) & 0xffffffffL;
      if ((off & 0x80000000L) != 0) {       // 2 GiB 넘는 자리의 표
        off = b.getLong(big + 8 * (int) (off & 0x7fffffff));
      }
      out.add(new IdxEntry(HEX.formatHex(data, names + 20 * k,
          names + 20 * k + 20), off,
          b.getInt(crcs + 4 * k) & 0xffffffffL));
    }
    return new Idx(out, Arrays.copyOfRange(data, data.length - 40,
        data.length - 20));
  }

  // 항목들 → 색인 판 2 바이트(SPEC.md §13.2).
  //
  // 이름 차례로 정렬한 fanout·이름·CRC·자리, 팩 체크섬, 그 앞 전부의
  // SHA-1. 같은 팩이면 git 의 .idx 와 바이트까지 같다.
  public static byte[] writeIdx(List<PackEntry> entries,
      byte[] packSum) {
    List<PackEntry> ents = entries.stream()
        .sorted(Comparator.comparing(e -> e.oid)).toList();
    List<Long> big = ents.stream().map(e -> e.offset)
        .filter(o -> o >= 0x80000000L).toList();
    int n = ents.size();
    ByteBuffer b = ByteBuffer.allocate(8 + 1024 + 28 * n
        + 8 * big.size() + 40);
    b.putInt(0xff744f63).putInt(2);
    int[] fan = new int[256];
    for (PackEntry e : ents) fan[Integer.parseInt(e.oid, 0, 2, 16)]++;
    for (int k = 0, sum = 0; k < 256; k++) b.putInt(sum += fan[k]);
    ents.forEach(e -> b.put(HEX.parseHex(e.oid)));
    ents.forEach(e -> b.putInt((int) e.crc));
    ents.forEach(e -> b.putInt(e.offset >= 0x80000000L
        ? 0x80000000 | big.indexOf(e.offset) : (int) e.offset));
    big.forEach(b::putLong);
    b.put(packSum);
    b.put(sha1Of(b.array(), b.position()));
    return b.array();
  }

  private static void varintOut(ByteArrayOutputStream out, long n) {
    do {
      int b = (int) (n & 0x7f);
      n >>>= 7;
      out.write(b | (n != 0 ? 0x80 : 0));
    } while (n != 0);
  }

  // 복사 명령 — 0 이 아닌 바이트만 쓴다. 길이 0x10000 은 길이 바이트
  // 없이.
  private static void copyOp(ByteArrayOutputStream out, int off,
      int n) {
    int op = 0x80;
    ByteArrayOutputStream tail = new ByteArrayOutputStream();
    for (int k = 0; k < 4; k++) {
      int b = (off >>> (8 * k)) & 0xff;
      if (b != 0) {
        op |= 1 << k;
        tail.write(b);
      }
    }
    for (int k = 0; k < 3 && n != 0x10000; k++) {
      int b = (n >>> (8 * k)) & 0xff;
      if (b != 0) {
        op |= 0x10 << k;
        tail.write(b);
      }
    }
    out.write(op);
    out.writeBytes(tail.toByteArray());
  }

  // 모아 둔 끼울 바이트를 127 바이트씩 끊어 내보낸다
  private static void flush(ByteArrayOutputStream out,
      ByteArrayOutputStream pend) {
    byte[] p = pend.toByteArray();
    for (int k = 0; k < p.length; k += 127) {
      int len = Math.min(127, p.length - k);
      out.write(len);
      out.write(p, k, len);
    }
    pend.reset();
  }

  // 바탕 → 결과의 델타(SPEC.md §13.3). 다섯 언어가 같은 바이트를
  // 낸다.
  //
  // 바탕을 16바이트 칸으로 잘라 "칸 내용 → 처음 나온 자리" 표를
  // 만들고, 결과를 앞에서부터 훑으며 표에 있는 칸이면 앞으로 늘일 수
  // 있는 만큼 복사, 없으면 한 바이트씩 끼울 것에 모은다. git 의 델타
  // 찾기(rolling hash 와 바탕 뒤로 늘이기)보다 단순하고, 그래서 보통
  // 더 길다. O(결과 길이 × 복사 길이) 최악.
  public static byte[] makeDelta(byte[] base, byte[] target) {
    String bs = new String(base, ISO_8859_1);
    String ts = new String(target, ISO_8859_1);
    Map<String, Integer> table = new HashMap<>();
    for (int off = 0; off + BLOCK <= base.length; off += BLOCK) {
      table.putIfAbsent(bs.substring(off, off + BLOCK), off);
    }
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    varintOut(out, base.length);
    varintOut(out, target.length);
    ByteArrayOutputStream pend = new ByteArrayOutputStream();
    for (int i = 0; i < target.length;) {
      Integer o = i + BLOCK <= target.length
          ? table.get(ts.substring(i, i + BLOCK)) : null;
      if (o == null) {
        pend.write(target[i++]);
        if (pend.size() == 127) flush(out, pend);
        continue;
      }
      int n = BLOCK;
      while (o + n < base.length && i + n < target.length
          && base[o + n] == target[i + n]) {
        n++;
      }
      flush(out, pend);
      for (int k = 0; k < n; k += 0x10000) {
        copyOp(out, o + k, Math.min(0x10000, n - k));
      }
      i += n;
    }
    flush(out, pend);
    return out.toByteArray();
  }

  private static byte[] entryHead(int type, long size) {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    int b = (int) ((type << 4) | (size & 15));
    for (size >>>= 4; size != 0; size >>>= 7) {
      out.write(b | 0x80);
      b = (int) (size & 0x7f);
    }
    out.write(b);
    return out.toByteArray();
  }

  // OFS_DELTA 거리 — 큰 쪽부터, 이어지는 바이트마다 1 을 뺀다.
  private static byte[] ofsOut(long n) {
    ByteArrayOutputStream rev = new ByteArrayOutputStream();
    rev.write((int) (n & 0x7f));
    for (n >>>= 7; n != 0; n >>>= 7) {
      n--;
      rev.write((int) (0x80 | (n & 0x7f)));
    }
    byte[] r = rev.toByteArray();
    byte[] out = new byte[r.length];
    for (int k = 0; k < r.length; k++) out[k] = r[r.length - 1 - k];
    return out;
  }

  // pack-objects 가 넣을 것 하나 — 형식, 몸, 델타 바탕의 목록
  // 번호(없으면 -1). 바탕은 목록에서 앞에 있어야 한다(OFS_DELTA).
  public record Item(String type, byte[] body, int base) {}

  public record Written(byte[] data, List<PackEntry> ents) {}

  public static Written writePack(List<Item> items) {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    out.writeBytes(ByteBuffer.allocate(12)
        .put("PACK".getBytes(ISO_8859_1)).putInt(2)
        .putInt(items.size()).array());
    List<PackEntry> ents = new ArrayList<>();
    for (Item it : items) {
      PackEntry e = new PackEntry();
      e.offset = out.size();
      e.type = it.type();
      e.body = it.body();
      e.oid = Objects.hashObject(e.type, e.body);
      byte[] raw = e.body;
      ByteArrayOutputStream one = new ByteArrayOutputStream();
      if (it.base() < 0) {
        e.packedType = TYPE_NAMES.indexOf(e.type);
        one.writeBytes(entryHead(e.packedType, raw.length));
      } else {
        PackEntry b = ents.get(it.base());
        raw = e.delta = makeDelta(b.body, e.body);
        e.packedType = OFS_DELTA;
        e.base = b.oid;
        e.depth = b.depth + 1;
        one.writeBytes(entryHead(OFS_DELTA, raw.length));
        one.writeBytes(ofsOut(e.offset - b.offset));
      }
      one.writeBytes(Zlib.compress(raw));
      byte[] bytes = one.toByteArray();
      e.crc = crc(bytes, 0, bytes.length);
      out.writeBytes(bytes);
      e.end = out.size();
      ents.add(e);
    }
    byte[] body = out.toByteArray();
    out.writeBytes(sha1Of(body, body.length));
    return new Written(out.toByteArray(), ents);
  }

  // git verify-pack -v 와 바이트까지 같은 줄들(SPEC.md §13.3).
  public static List<String> verifyLines(List<PackEntry> entries,
      String packPath) {
    List<PackEntry> ents = entries.stream()
        .sorted(Comparator.comparingLong(e -> e.offset)).toList();
    List<String> rows = new ArrayList<>();
    TreeMap<Integer, Integer> hist = new TreeMap<>();
    for (int k = 0; k < ents.size(); k++) {
      PackEntry e = ents.get(k);
      long next = k + 1 < ents.size() ? ents.get(k + 1).offset : e.end;
      // 크기는 팩에 적힌 크기 — 델타면 델타의 크기다(git 과 같다)
      int size = (e.delta != null ? e.delta : e.body).length;
      rows.add(String.format("%s %-6s %d %d %d", e.oid, e.type, size,
          next - e.offset, e.offset)
          + (e.depth > 0 ? " " + e.depth + " " + e.base : ""));
      hist.merge(e.depth, 1, Integer::sum);
    }
    Function<Integer, String> plural = n -> n + " object"
        + (n == 1 ? "" : "s");
    rows.add("non delta: " + plural.apply(hist.getOrDefault(0, 0)));
    hist.remove(0);
    hist.forEach((d, n) ->
        rows.add("chain length = " + d + ": " + plural.apply(n)));
    rows.add(packPath + ": ok");
    return rows;
  }
}
