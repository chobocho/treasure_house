package mygit.tests;

import static java.nio.charset.StandardCharsets.ISO_8859_1;
import static java.nio.charset.StandardCharsets.UTF_8;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

// 시험 도우미 — golden/ 을 읽고 재료를 바이트로 만든다.
//
// golden/ 은 진짜 git 이 만든 기준 바이트다(SPEC.md §16.2). 시험은 git
// 을 부르지 않고 이 파일들만 읽는다. 재료 문법은 SPEC.md §2.1·§16.4
// 이고, tools/make_golden.py 의 make() 와 같은 규칙이다.
final class Golden {
  // 짓고 나면 이 클래스는 build/java/ 에 있다 — git/ 은 둘 위다
  static final Path GOLDEN = where().resolve("golden");

  private Golden() {}

  private static Path where() {
    try {
      return Path.of(Golden.class.getProtectionDomain().getCodeSource()
          .getLocation().toURI()).getParent().getParent();
    } catch (java.net.URISyntaxException e) {
      throw new IllegalStateException(e);
    }
  }

  static String path(String... parts) {
    return GOLDEN.resolve(String.join("/", parts)).toString();
  }

  static byte[] read(String... parts) throws IOException {
    return Files.readAllBytes(Path.of(path(parts)));
  }

  // 주석(#)과 머리 줄을 뺀 행들. 각 행은 칸 이름 → 값.
  static List<Map<String, String>> tsv(String... parts)
      throws IOException {
    List<Map<String, String>> rows = new ArrayList<>();
    String[] head = null;
    for (String line : new String(read(parts), UTF_8).split("\n")) {
      if (line.isEmpty() || line.startsWith("#")) continue;
      String[] cols = line.split("\t", -1);
      if (head == null) {
        head = cols;
        continue;
      }
      Map<String, String> row = new HashMap<>();
      for (int i = 0; i < Math.min(head.length, cols.length); i++) {
        row.put(head[i], cols[i]);
      }
      rows.add(row);
    }
    return rows;
  }

  // 시험마다 새 임시 디렉터리. 지우는 쪽은 rmTree.
  static String tempdir() throws IOException {
    return Files.createTempDirectory("mygit-").toString();
  }

  static void rmTree(String dir) throws IOException {
    try (var s = Files.walk(Path.of(dir))) {
      for (Path p : s.sorted(java.util.Comparator.reverseOrder())
          .toList()) {
        Files.delete(p);
      }
    }
  }

  // 유니코드 문자열 → 바이트 문자열(UTF-8 바이트를 latin1 로). mygit
  // 안의 문자열은 전부 이 꼴이다(Main.byteNames).
  static String b(String s) {
    return new String(s.getBytes(UTF_8), ISO_8859_1);
  }

  // text: 재료의 이스케이프 — \n \t \\ \" \xHH.
  static byte[] unescape(String s) {
    byte[] raw = s.getBytes(UTF_8);
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    for (int i = 0; i < raw.length; i++) {
      if (raw[i] != '\\' || i + 1 >= raw.length) {
        out.write(raw[i]);
      } else if (raw[++i] == 'x') {
        out.write(Integer.parseInt(new String(raw, i + 1, 2, UTF_8),
            16));
        i += 2;
      } else {
        out.write(raw[i] == 'n' ? 10 : raw[i] == 't' ? 9 : raw[i]);
      }
    }
    return out.toByteArray();
  }

  // 재료 한 줄 → 바이트 (SPEC.md §2.1). O(결과 길이).
  static byte[] make(String recipe) throws IOException {
    int at = recipe.indexOf(':');
    String kind = at < 0 ? recipe : recipe.substring(0, at);
    String arg = at < 0 ? "" : recipe.substring(at + 1);
    String[] ab = arg.split(":");
    switch (kind) {
      case "empty": return new byte[0];
      case "text": return unescape(arg);
      case "repeat": {
        byte[] out = new byte[Integer.parseInt(ab[1])];
        java.util.Arrays.fill(out, (byte) Integer.parseInt(ab[0], 16));
        return out;
      }
      case "counter": {
        byte[] out = new byte[Integer.parseInt(arg)];
        for (int i = 0; i < out.length; i++) out[i] = (byte) (i % 251);
        return out;
      }
      case "seq": {
        StringBuilder sb = new StringBuilder();
        int b = Integer.parseInt(ab[1]);
        for (int i = Integer.parseInt(ab[0]); i <= b; i++) {
          sb.append(i).append('\n');
        }
        return sb.toString().getBytes(UTF_8);
      }
      case "golden": return read(arg);
      default:
        throw new IllegalArgumentException("모르는 재료: " + recipe);
    }
  }
}
