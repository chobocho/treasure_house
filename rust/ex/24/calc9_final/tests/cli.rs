use std::io::Write;
use std::process::{Command, Stdio};

// Cargo 가 넣어 주는 값 — 이 패키지의 실행 파일 calc 의 경로
const EXE: &str = env!("CARGO_BIN_EXE_calc");

// 실행 파일을 띄워 표준 입력에 바이트를 먹이고,
// 종료 코드와 두 출력을 받는다
fn launch(
    args: &[&str],
    input: &[u8],
) -> (Option<i32>, String, String) {
    let mut child = Command::new(EXE)
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    // 블록이 끝나면 손잡이가 정리돼 자식의 표준 입력이 닫힌다
    {
        let mut stdin = child.stdin.take().unwrap();
        stdin.write_all(input).unwrap();
    }
    let out = child.wait_with_output().unwrap();
    let stdout = String::from_utf8(out.stdout).unwrap();
    let stderr = String::from_utf8(out.stderr).unwrap();
    (out.status.code(), stdout, stderr)
}

#[test]
fn lines_from_stdin_exit_zero() {
    let (code, out, err) = launch(&[], b"2 + 3 * 4\n\n(2 + 3) * 4\n");
    assert_eq!(
        (code, out.as_str(), err.as_str()),
        (Some(0), "14\n20\n", "")
    );
}

#[test]
fn error_line_exits_one() {
    let (code, out, err) = launch(&["1 / 0", "6 * 7"], b"");
    assert_eq!((code, out.as_str()), (Some(1), "42\n"));
    assert_eq!(err, "calc: 0 으로 나눌 수 없다 (자리 2)\n1 / 0\n  ^\n");
}

#[test]
fn unreadable_stdin_exits_two() {
    let (code, out, err) = launch(&[], b"1 + 1\n\xff\n2 + 2\n");
    assert_eq!((code, out.as_str()), (Some(2), "2\n"));
    // 까닭은 표준 라이브러리가 정하는 글이라 앞머리만 본다
    assert!(err.starts_with("calc: "));
    assert_eq!(err.lines().count(), 1);
}
