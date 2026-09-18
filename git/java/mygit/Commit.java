package mygit;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

// commit·tag 객체와 신원 줄 (SPEC.md §4.4 · §4.5 · §1.3 · §9.1).
//
// 커밋 = 트리 하나 + 부모 목록 + 누가·언제 + 메시지. 커밋의 이름에는
// 작성 시각과 시간대까지 들어가므로, 같은 트리라도 1초만 달라도 다른
// 커밋이다 — 그래서 mygit 은 시계를 읽지 않고 환경 변수만 믿는다.
//
// 몸은 latin1 로 풀고 latin1 로 싼다 — 메시지의 UTF-8 바이트가 글자
// 하나씩으로 그대로 지나가므로 깨진 바이트도 되돌릴 수 있다.
public final class Commit {
  private static final String[] DAYS =
      {"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"};
  private static final String[] MONTHS = {"Jan", "Feb", "Mar", "Apr",
      "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};
  private static final Pattern IDENT =
      Pattern.compile("^(.*) <(.*)> (-?\\d+) ([+-]\\d{4})$");

  private Commit() {}

  // 신원 줄 하나 — 이름, 메일, 초, 시간대
  public record Ident(String name, String mail, long secs, String tz) {}

  public record CommitObj(String tree, List<String> parents,
      String author, String committer, String message) {}

  // "이름 <메일> 초 ±hhmm" → Ident.
  public static Ident parseIdent(String line) {
    Matcher m = IDENT.matcher(line);
    if (!m.matches()) {
      throw new GitError("fatal: mygit: bad ident line: " + line);
    }
    return new Ident(m.group(1), m.group(2), Long.parseLong(m.group(3)),
        m.group(4));
  }

  // GIT_<who>_NAME·EMAIL·DATE → 신원 줄 (SPEC.md §1.3).
  //
  // 설정 파일도 시계도 보지 않는다 — 없으면 멈춘다. 캡처가 세 번
  // 같으려면 입력이 전부 드러나 있어야 하기 때문이다.
  public static String identFromEnv(Map<String, String> env,
      String who) {
    List<String> vals = new ArrayList<>();
    for (String part : List.of("NAME", "EMAIL", "DATE")) {
      String key = "GIT_" + who + "_" + part;
      if (!env.containsKey(key)) {
        throw new GitError("fatal: mygit: " + key + " is not set");
      }
      vals.add(env.get(key));
    }
    if (!vals.get(2).matches("\\d+ [+-]\\d{4}")) {
      throw new GitError("fatal: mygit: GIT_" + who
          + "_DATE is not '<seconds> <+hhmm>'");
    }
    return vals.get(0) + " <" + vals.get(1) + "> " + vals.get(2);
  }

  // git log 의 Date 꼴 — "Wed Nov 15 07:13:20 2023 +0900".
  //
  // 시각을 그 시간대로 옮겨 찍는다. 일은 앞에 0 을 붙이지 않는다.
  // 달력은 Howard Hinnant 의 civil-from-days 공식 — 로캘도 표준 날짜
  // 함수도 쓰지 않는다. O(1).
  public static String formatDate(long seconds, String tz) {
    int sign = tz.charAt(0) == '-' ? -1 : 1;
    long local = seconds + sign * (Integer.parseInt(tz.substring(1, 3))
        * 3600 + Integer.parseInt(tz.substring(3, 5)) * 60);
    long days = Math.floorDiv(local, 86400);
    long rest = Math.floorMod(local, 86400);
    long z = days + 719468;
    long era = Math.floorDiv(z, 146097);
    long doe = z - era * 146097;
    long yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    long doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    long mp = (5 * doy + 2) / 153;
    long d = doy - (153 * mp + 2) / 5 + 1;
    long m = mp < 10 ? mp + 3 : mp - 9;
    long y = yoe + era * 400 + (m <= 2 ? 1 : 0);
    return String.format("%s %s %d %02d:%02d:%02d %d %s",
        DAYS[Math.floorMod(days + 4, 7)], MONTHS[(int) m - 1], d,
        rest / 3600, rest / 60 % 60, rest % 60, y, tz);
  }

  // commit -m 의 공백 정리(git 의 cleanup=whitespace).
  //
  // 줄마다 끝 공백을 지우고, 이어진 빈 줄은 하나로, 앞뒤의 빈 줄은
  // 지운다. 줄 앞의 공백은 남긴다. 남는 것이 없으면 "".
  public static String cleanupMessage(String text) {
    List<String> out = new ArrayList<>();
    for (String line : text.split("\n", -1)) {
      line = line.stripTrailing();
      if (!line.isEmpty()
          || (!out.isEmpty() && !out.get(out.size() - 1).isEmpty())) {
        out.add(line);
      }
    }
    while (!out.isEmpty() && out.get(out.size() - 1).isEmpty()) {
      out.remove(out.size() - 1);
    }
    return out.isEmpty() ? "" : String.join("\n", out) + "\n";
  }

  // 제목 = 첫 문단의 줄들을 공백 하나로 이은 것(SPEC.md §4.4).
  //
  // 줄 끝의 공백은 떼지만 **앞의 공백은 남긴다** — "  lead" 라는
  // 메시지의 제목은 "  lead" 다(진짜 git 의 commit 요약 줄로 확인,
  // golden/scen/plumbing.scn). 빈 줄을 만나면 거기서 끝난다.
  public static String subjectOf(String message) {
    List<String> lines = new ArrayList<>();
    for (String line : message.split("\n", -1)) {
      if (line.isBlank()) break;
      lines.add(line.stripTrailing());
    }
    return String.join(" ", lines);
  }

  // 커밋 몸 → CommitObj. 모르는 머리 줄(gpgsig·mergetag 와 그 이어진
  // 줄)은 건너뛴다.
  public static CommitObj parseCommit(byte[] body) {
    String text = new String(body, ISO_8859_1);
    int cut = text.indexOf("\n\n");
    String head = cut < 0 ? text : text.substring(0, cut);
    String tree = null;
    String author = null;
    String committer = null;
    List<String> parents = new ArrayList<>();
    for (String line : head.split("\n")) {
      String[] kv = line.split(" ", 2);
      String val = kv.length > 1 ? kv[1] : "";
      switch (kv[0]) {
        case "tree" -> tree = val;
        case "parent" -> parents.add(val);
        case "author" -> author = val;
        case "committer" -> committer = val;
        default -> { }
      }
    }
    if (tree == null || committer == null) {
      throw new GitError("fatal: mygit: corrupt commit object");
    }
    return new CommitObj(tree, parents, author, committer,
        cut < 0 ? "" : text.substring(cut + 2));
  }

  public static byte[] serializeCommit(String tree,
      List<String> parents, String author, String committer,
      String message) {
    StringBuilder sb = new StringBuilder("tree " + tree + "\n");
    parents.forEach(p -> sb.append("parent ").append(p).append('\n'));
    sb.append("author ").append(author).append("\ncommitter ")
        .append(committer).append("\n\n").append(message);
    return sb.toString().getBytes(ISO_8859_1);
  }

  public static byte[] serializeTag(String obj, String type,
      String name, String tagger, String message) {
    return ("object " + obj + "\ntype " + type + "\ntag " + name
        + "\ntagger " + tagger + "\n\n" + message).getBytes(ISO_8859_1);
  }
}
