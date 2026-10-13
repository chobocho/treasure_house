use std::io::{self, Write};

// run 을 프로세스 없이 부른다. 표준 입력 자리에는 &[u8] 를,
// 표준 출력과 표준 오류 자리에는 Vec<u8> 를 넣는다
fn run_calc(args: &[&str], stdin: &str) -> (u8, String, String) {
    let args: Vec<String> =
        args.iter().map(|a| a.to_string()).collect();
    let mut out = Vec::new();
    let mut err = Vec::new();
    let code =
        calc::run(&args, stdin.as_bytes(), &mut out, &mut err).unwrap();
    let out = String::from_utf8(out).unwrap();
    let err = String::from_utf8(err).unwrap();
    (code, out, err)
}

#[test]
fn each_line_gets_a_value_or_a_notice() {
    // 둘째 줄은 비었고, 마지막 줄은 줄바꿈 없이 끝난다
    let (code, out, err) = run_calc(&[], "1 + 1\n\n2 *\n3 * 3");
    assert_eq!((code, out.as_str()), (1, "2\n9\n"));
    let want = concat!(
        "calc: 수나 괄호가 올 자리에서 줄이 끝났다 (자리 3)\n",
        "2 *\n",
        "   ^\n",
    );
    assert_eq!(err, want);
}

#[test]
fn lines_without_errors_exit_zero() {
    // 줄 끝의 \r\n 은 줄에 들지 않는다
    let (code, out, err) = run_calc(&[], "1 + 1\r\n-7 / 2\r\n");
    assert_eq!((code, out.as_str(), err.as_str()), (0, "2\n-3\n", ""));
    // 빈 입력과, 값이 없는 줄뿐인 입력
    assert_eq!(run_calc(&[], ""), (0, String::new(), String::new()));
    assert_eq!(
        run_calc(&[], "\n \t\n"),
        (0, String::new(), String::new())
    );
}

#[test]
fn arguments_are_lines_too() {
    // 인자가 있으면 표준 입력은 읽지 않는다
    let (code, out, err) = run_calc(&["2 + 3", "4 *"], "6 * 7\n");
    assert_eq!((code, out.as_str()), (1, "5\n"));
    assert!(err.starts_with("calc: 수나 괄호가 올 자리에서"));
    // 인자 안의 줄바꿈도 줄을 가르고, 빈 인자에는 줄이 없다
    let (code, out, err) = run_calc(&["1\n2\r\n3", ""], "");
    assert_eq!(
        (code, out.as_str(), err.as_str()),
        (0, "1\n2\n3\n", "")
    );
    // 옵션은 없다. -h 도 식으로 읽는다
    let (code, _, err) = run_calc(&["-h"], "");
    assert_eq!(code, 1);
    assert!(err.starts_with("calc: 모르는 글자 (자리 1)\n"));
}

#[test]
fn odd_characters_and_long_lines() {
    // NUL 바이트는 모르는 글자다
    let (code, _, err) = run_calc(&[], "1 \0 2\n");
    assert_eq!(code, 1);
    assert!(err.starts_with("calc: 모르는 글자 (자리 2)\n"));
    // 빈칸 십만 개 뒤의 수 하나
    let line = " ".repeat(100_000) + "7\n";
    assert_eq!(run_calc(&[], &line).1, "7\n");
    // 숫자 십만 개, 그리고 수 십만 개
    let (_, _, err) = run_calc(&[], &"9".repeat(100_000));
    assert!(err.starts_with("calc: 수가 너무 크다 (자리 0)\n"));
    let (_, _, err) = run_calc(&[], &"1 ".repeat(100_000));
    assert!(err.starts_with("calc: 토큰이 너무 많다 (자리 400)\n"));
    // 토큰이 꼭 200 개인 줄은 값까지 간다. 부호 199 개와 1 이다
    let line = "-".repeat(199) + "1";
    assert_eq!(run_calc(&[], &line).1, "-1\n");
    // 1 을 백 번 더한 줄 — 토큰 199 개, 나무의 깊이 100
    let line = "1".to_string() + &"+1".repeat(99);
    assert_eq!(run_calc(&[], &line).1, "100\n");
}

#[test]
fn bad_utf8_stops_after_earlier_answers() {
    let stdin = &b"1 + 1\n\xff\n2 + 2\n"[..];
    let mut out = Vec::new();
    let mut err = Vec::new();
    let got = calc::run(&[], stdin, &mut out, &mut err);
    assert_eq!(got.unwrap_err().kind(), io::ErrorKind::InvalidData);
    // 깨진 줄 앞의 답은 이미 썼고, 뒤의 줄은 읽지 않았다
    assert_eq!(out, b"2\n");
    assert!(err.is_empty());
}

// 무엇을 쓰라고 하든 실패하는 쓸 곳
struct Broken;

impl Write for Broken {
    fn write(&mut self, _buf: &[u8]) -> io::Result<usize> {
        Err(io::Error::other("닫힌 출력"))
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[test]
fn write_failure_comes_back_as_err() {
    let mut sink = Vec::new();
    let stdin = "1 + 1\n".as_bytes();
    let got = calc::run(&[], stdin, &mut Broken, &mut sink);
    assert_eq!(got.unwrap_err().to_string(), "닫힌 출력");
    // 값이 없는 줄뿐이면 쓰지 않으므로 실패도 없다
    let got =
        calc::run(&[], "\n \n".as_bytes(), &mut Broken, &mut sink);
    assert_eq!(got.unwrap(), 0);
    // 알림을 쓰지 못해도 Err 로 돌아온다
    let got =
        calc::run(&[], "1 +\n".as_bytes(), &mut sink, &mut Broken);
    assert_eq!(got.unwrap_err().to_string(), "닫힌 출력");
    assert!(sink.is_empty());
}
