use std::io::{self, Write};

// run 을 프로세스 없이 부른다. 표준 입력 자리에는 &[u8] 를,
// 표준 출력과 표준 오류 자리에는 Vec<u8> 를 넣는다
fn run_grep(args: &[&str], stdin: &str) -> (u8, String, String) {
    let args: Vec<String> =
        args.iter().map(|a| a.to_string()).collect();
    let mut out = Vec::new();
    let mut err = Vec::new();
    let code =
        grep::run(&args, stdin.as_bytes(), &mut out, &mut err).unwrap();
    let out = String::from_utf8(out).unwrap();
    let err = String::from_utf8(err).unwrap();
    (code, out, err)
}

#[test]
fn stdin_lines_have_no_name() {
    // 입력의 마지막 줄은 줄바꿈 없이 끝난다
    let (code, out, err) = run_grep(&["-n", "b"], "ab\nc\nb");
    assert_eq!((code, out.as_str()), (0, "1:ab\n3:b\n"));
    assert_eq!(err, "");
}

#[test]
fn no_selected_line_is_exit_one() {
    let (code, out, err) = run_grep(&["z"], "ab\nc\n");
    assert_eq!((code, out.as_str(), err.as_str()), (1, "", ""));
    // -c 가 0 을 써도, 고른 줄이 없으면 1 이다
    let (code, out, _) = run_grep(&["-c", "z"], "ab\nc\n");
    assert_eq!((code, out.as_str()), (1, "0\n"));
    // 빈 패턴이라도 입력에 줄이 없으면 1 이다
    let (code, out, _) = run_grep(&[""], "");
    assert_eq!((code, out.as_str()), (1, ""));
}

#[test]
fn missing_pattern_writes_usage_to_err_only() {
    let (code, out, err) = run_grep(&["-i"], "ab\n");
    assert_eq!((code, out.as_str()), (2, ""));
    assert_eq!(err, format!("grep: 패턴이 없다\n{}\n", grep::USAGE));
}

#[test]
fn unreadable_file_does_not_stop_the_rest() {
    let args =
        ["rust", "data/todo.txt", "data/none.txt", "data/memo.txt"];
    let (code, out, err) = run_grep(&args, "");
    // 고른 줄이 있어도, 읽지 못한 파일이 있으면 2 다
    assert_eq!(code, 2);
    let want = [
        "data/todo.txt:rust book 읽기\n",
        "data/memo.txt:녹은 영어로 rust 다\n",
        "data/memo.txt:trust 안에도 rust 가 있다\n",
    ]
    .concat();
    assert_eq!(out, want);
    // 운영 체제가 주는 까닭은 견주지 않는다
    assert!(err.starts_with("grep: data/none.txt: "));
}

#[test]
fn same_file_twice_is_searched_twice() {
    let args = ["-c", "milk", "data/todo.txt", "data/todo.txt"];
    let (code, out, _) = run_grep(&args, "");
    let want = "data/todo.txt:1\ndata/todo.txt:1\n";
    assert_eq!((code, out.as_str()), (0, want));
}

#[test]
fn stdin_that_is_not_text_comes_back_as_err() {
    let args = ["a".to_string()];
    let mut out = Vec::new();
    let mut err = Vec::new();
    // 둘째 줄의 \xff 는 UTF-8 이 될 수 없는 바이트다
    let stdin = &b"a\n\xff\n"[..];
    let got = grep::run(&args, stdin, &mut out, &mut err);
    assert_eq!(got.unwrap_err().kind(), io::ErrorKind::InvalidData);
    // 깨진 바이트 앞의 줄도 쓰이지 않았다
    assert!(out.is_empty() && err.is_empty());
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
    let mut err = Vec::new();
    let args = ["a".to_string()];
    let stdin = "a\n".as_bytes();
    let got = grep::run(&args, stdin, &mut Broken, &mut err);
    assert_eq!(got.unwrap_err().to_string(), "닫힌 출력");
    // 고른 줄이 없으면 쓰지 않으므로 실패도 없다
    let args = ["z".to_string()];
    let got = grep::run(&args, stdin, &mut Broken, &mut err);
    assert_eq!(got.unwrap(), 1);
    // 알림을 쓰지 못해도 Err 로 돌아온다
    let got = grep::run(&[], stdin, &mut err, &mut Broken);
    assert_eq!(got.unwrap_err().to_string(), "닫힌 출력");
}
