package compresslib;

/**
 * 손상된 입력에서 던지는 예외 — SPEC §12.
 *
 * <p>조용히 그럴듯한 바이트를 내놓는 복호기가 압축에서는 가장 위험하다.
 * 검사되지 않은 길이로 할당하거나, 범위 밖을 읽거나, 영영 안 끝나는
 * 일이 없도록 복호기마다 막아 두고 여기로 모은다.
 *
 * <p>검사 예외(checked)가 아니라 실행 예외다. 복호기 안쪽은 "여기서 더
 * 못 간다" 는 자리가 수십 군데라, 전부 throws 로 위로 나르면 알고리즘이
 * 오류 처리에 묻힌다 — 가르치는 글에 실릴 코드로는 최악이다.
 */
public class CodecException extends RuntimeException {
  private static final long serialVersionUID = 1L;

  public CodecException(String message) {
    super(message);
  }

  /** 던지는 자리를 짧게 쓰기 위한 도우미. */
  public static CodecException of(String fmt, Object... args) {
    return new CodecException(String.format(fmt, args));
  }
}
