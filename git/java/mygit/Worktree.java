package mygit;

// 작업 트리 (SPEC.md §8 · §9.3) — 경로 따옴표, 훑기, status, 바꾸기.
//
// status 는 세 가지를 견준다: HEAD 트리, 인덱스, 디스크의 파일. 두 칸
// 글자(XY)가 곧 "어느 두 곳이 다른가" 다 — X 는 HEAD 와 인덱스, Y 는
// 인덱스와 작업 트리. 6부가 이 세 영역을 명령마다 캡처로 보인다.
public final class Worktree {
  private Worktree() {}

  // \a \b \t \n \v \f \r (7‥13)와 따옴표·역슬래시는 두 글자로 쓴다
  private static final String SHORT = "abtnvfr";

  // 경로 바이트 → git 이 사람에게 찍는 꼴 (core.quotePath=true).
  //
  // 제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
  // 전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space 는
  // status 의 규칙 — 공백만 있어도 감싼다(공백 자체는 그대로).
  // 한글은 UTF-8 여섯 바이트가 \355\225… 로 찍힌다. O(경로 길이).
  public static String quotePath(String p, boolean space) {
    boolean need = space && p.contains(" ");
    StringBuilder body = new StringBuilder();
    for (char b : p.toCharArray()) {
      if (b == '"' || b == '\\') {
        body.append('\\').append(b);
      } else if (b >= 7 && b <= 13) {
        body.append('\\').append(SHORT.charAt(b - 7));
      } else if (b < 32 || b >= 127) {
        body.append(String.format("\\%03o", (int) b));
      } else {
        body.append(b);
        continue;
      }
      need = true;
    }
    return need ? "\"" + body + "\"" : body.toString();
  }

  public static String quotePath(String p) {
    return quotePath(p, false);
  }
}
