package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;

// 인덱스 (SPEC.md §7) — .git/index, 다음 커밋이 될 트리의 초안.
//
// 작업 트리와 저장소 사이의 이 파일 하나가 "스테이징" 의 실체다.
// 항목마다 경로·모드·blob 이름과 함께 파일의 stat 칸(시각·크기·inode)
// 을 적어 두는데, git 은 그것으로 "안 바뀐 파일" 을 해시 없이 가려낸다.
// mygit 은 칸을 채워 두기만 하고 자신은 믿지 않는다(§7.2) — 늘
// 해시한다.
//
// 판 2 로 쓰고, 판 2·3 을 읽는다. 확장(TREE·REUC…)은 읽을 때 건너뛰고
// 쓰지 않는다. 수는 전부 빅 엔디언 — ByteBuffer 의 기본값이다.
public final class Index {
  private static final int ENTRY = 62;  // stat 10칸 · 이름 20 · flags 2
  private static final int MAX_NAME = 0xfff;

  private Index() {}

  // 인덱스 항목 하나. 경로는 바이트 문자열, 이름은 16진 40글자.
  // stat 칸은 32비트 부호 없는 수지만 int 에 비트 그대로 담는다.
  public static final class IndexEntry {
    public String path;
    public String oid;
    public int mode;
    public int stage;
    public int size;
    public int ctimeS, ctimeNs, mtimeS, mtimeNs, dev, ino, uid, gid;
    public boolean assumeValid, skipWorktree;

    public IndexEntry(String path, String oid, int mode, int stage) {
      this.path = path;
      this.oid = oid;
      this.mode = mode;
      this.stage = stage;
    }
  }

  // 작업 트리 파일의 stat 으로 항목을 채운다(SPEC.md §7.2).
  //
  // 모드는 소유자 실행 비트만 본다 — git 과 같다(그룹·기타는 버린다).
  // dev·ino·size 는 32비트로 자른다. "unix:*" 속성이 stat(2) 의 칸을
  // 나노초까지 준다.
  public static IndexEntry entryFromStat(String path, String full,
      String oid) {
    Map<String, Object> st;
    try {
      st = Files.readAttributes(Path.of(full), "unix:*");
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
    int perm = (Integer) st.get("mode");
    IndexEntry e = new IndexEntry(path, oid,
        (perm & 0100) != 0 ? 0100755 : 0100644, 0);
    e.size = (int) (long) (Long) st.get("size");
    var c = ((FileTime) st.get("ctime")).toInstant();
    var m = ((FileTime) st.get("lastModifiedTime")).toInstant();
    e.ctimeS = (int) c.getEpochSecond();
    e.ctimeNs = c.getNano();
    e.mtimeS = (int) m.getEpochSecond();
    e.mtimeNs = m.getNano();
    e.dev = (int) (long) (Long) st.get("dev");
    e.ino = (int) (long) (Long) st.get("ino");
    e.uid = (Integer) st.get("uid");
    e.gid = (Integer) st.get("gid");
    return e;
  }

  // 인덱스 바이트 → 항목들. 끝 SHA-1 이 틀리면 오류.
  //
  // 판 3 은 flags 의 비트 14 가 서 있는 항목 뒤에 2바이트 확장 flags
  // 가 더 있다(skip-worktree 가 거기 산다). O(파일 크기).
  public static List<IndexEntry> parseIndex(byte[] data) {
    GitError corrupt = new GitError("fatal: mygit: index file corrupt");
    int n = data.length;
    if (n < 32 || !new String(data, 0, 4, ISO_8859_1).equals("DIRC")
        || !Arrays.equals(Arrays.copyOfRange(data, n - 20, n),
            new Sha1().update(data, 0, n - 20).digest())) {
      throw corrupt;
    }
    ByteBuffer b = ByteBuffer.wrap(data);
    int ver = b.getInt(4);
    if (ver == 4) {
      throw new GitError("fatal: mygit: index v4 unsupported");
    }
    if (ver != 2 && ver != 3) {
      throw new GitError("fatal: mygit: index version " + ver);
    }
    List<IndexEntry> out = new ArrayList<>();
    int pos = 12;
    for (int k = b.getInt(8); k > 0; k--) {
      int flags = b.getShort(pos + 60) & 0xffff;
      IndexEntry e = new IndexEntry(null,
          HexFormat.of().formatHex(data, pos + 40, pos + 60),
          b.getInt(pos + 24), (flags >> 12) & 3);
      e.ctimeS = b.getInt(pos);
      e.ctimeNs = b.getInt(pos + 4);
      e.mtimeS = b.getInt(pos + 8);
      e.mtimeNs = b.getInt(pos + 12);
      e.dev = b.getInt(pos + 16);
      e.ino = b.getInt(pos + 20);
      e.uid = b.getInt(pos + 28);
      e.gid = b.getInt(pos + 32);
      e.size = b.getInt(pos + 36);
      e.assumeValid = (flags & 0x8000) != 0;
      int start = pos + ENTRY;
      if ((flags & 0x4000) != 0) {              // 판 3 의 확장 flags
        e.skipWorktree = (b.getShort(start) & 0x4000) != 0;
        start += 2;
      }
      int end = start;                   // 이름 길이 0xfff 넘어도
      while (data[end] != 0) end++;
      e.path = new String(data, start, end - start, ISO_8859_1);
      pos += (start - pos + e.path.length() + 8) / 8 * 8;
      out.add(e);
    }
    return out;
  }

  // 항목들 → 판 2 인덱스 바이트. 경로·단계 차례로 정렬한다.
  //
  // 항목 길이 = (62 + 이름 길이 + 8) & ~7 — 이름 뒤 NUL 이 1‥8 개.
  // 판 2 에는 확장 flags 가 없으므로 skip-worktree 는 여기서 사라진다
  // (mygit 은 그 비트를 쓰지 않는다 — 읽기만 한다).
  public static byte[] serializeIndex(List<IndexEntry> entries) {
    List<IndexEntry> ents = entries.stream().sorted(Comparator
        .comparing((IndexEntry e) -> e.path)
        .thenComparingInt(e -> e.stage)).toList();
    int total = 12 + 20;
    for (IndexEntry e : ents) {
      total += (ENTRY + e.path.length() + 8) & ~7;
    }
    ByteBuffer b = ByteBuffer.allocate(total);
    b.put("DIRC".getBytes(ISO_8859_1)).putInt(2).putInt(ents.size());
    for (IndexEntry e : ents) {
      int start = b.position();
      for (int v : new int[] {e.ctimeS, e.ctimeNs, e.mtimeS, e.mtimeNs,
          e.dev, e.ino, e.mode, e.uid, e.gid, e.size}) {
        b.putInt(v);
      }
      b.put(HexFormat.of().parseHex(e.oid));
      b.putShort((short) ((e.stage << 12)
          | Math.min(e.path.length(), MAX_NAME)
          | (e.assumeValid ? 0x8000 : 0)));
      b.put(e.path.getBytes(ISO_8859_1));
      // 남은 자리는 allocate 가 이미 0 으로 채워 두었다
      b.position(start + ((ENTRY + e.path.length() + 8) & ~7));
    }
    b.put(new Sha1().update(b.array(), 0, total - 20).digest());
    return b.array();
  }

  // .git/index 를 읽는다. 없으면(첫 add 전) 빈 목록.
  public static List<IndexEntry> readIndex(String gitdir) {
    byte[] data = Fs.readOrNull(Fs.join(gitdir, "index"));
    return data == null ? new ArrayList<>() : parseIndex(data);
  }

  // index.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §7.4).
  public static void writeIndex(String gitdir, List<IndexEntry> ents) {
    Fs.writeLocked(Fs.join(gitdir, "index"), serializeIndex(ents));
  }
}
