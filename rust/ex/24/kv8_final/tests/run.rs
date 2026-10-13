use std::fs;
use std::io::{self, Write};

use kv::KvError;

// 패키지 뿌리 — 컴파일할 때 정해지는 글
const ROOT: &str = env!("CARGO_MANIFEST_DIR");

// run 을 프로세스 없이 부른다. 표준 입력 자리에는 &[u8] 를,
// 표준 출력과 표준 오류 자리에는 Vec<u8> 를 넣는다
fn run_kv(args: &[&str], stdin: &str) -> (u8, String, String) {
    let args: Vec<String> =
        args.iter().map(|a| a.to_string()).collect();
    let mut out = Vec::new();
    let mut err = Vec::new();
    let code =
        kv::run(&args, stdin.as_bytes(), &mut out, &mut err).unwrap();
    let out = String::from_utf8(out).unwrap();
    let err = String::from_utf8(err).unwrap();
    (code, out, err)
}

// 시험마다 제 이름의 저장소 파일을 쓴다.
// 남아 있던 것은 지우고 시작한다
fn fresh(name: &str) -> String {
    let dir = format!("{ROOT}/target/kv-test");
    fs::create_dir_all(&dir).unwrap();
    let path = format!("{dir}/run-{name}.kv");
    let _ = fs::remove_file(&path);
    path
}

#[test]
fn memory_session_answers_line_by_line() {
    let input = "set a 1\nget a\nget b\n\nlst\nset a 2\nlist";
    let (code, out, err) = run_kv(&[], input);
    assert_eq!((code, out.as_str()), (1, "1\na\t2\n"));
    assert_eq!(
        err,
        "kv: 3번째 줄: 없는 키 b\n\
         kv: 5번째 줄: 모르는 명령이다\n"
    );
    // 줄 끝의 \r\n 은 값에 들어가지 않는다
    let (code, out, err) = run_kv(&[], "set a 1\r\nget a\r\n");
    assert_eq!((code, out.as_str(), err.as_str()), (0, "1\n", ""));
    // 빈 입력에는 답도 알림도 없다
    assert_eq!(run_kv(&[], ""), (0, String::new(), String::new()));
}

#[test]
fn empty_and_dash_arguments_are_refused() {
    let usage = "쓰는 법: kv [저장소파일 [명령파일 ...]]\n";
    for args in [&["--help"][..], &["-"], &[""], &["memo.kv", "-x"]] {
        let (code, out, err) = run_kv(args, "set a 1\n");
        assert_eq!((code, out.as_str(), err.as_str()), (2, "", usage));
    }
}

#[test]
fn file_store_remembers_between_runs() {
    let path = fresh("remember");
    let input = "set name 보리\nset tab a\tb\n";
    let (code, out, _) = run_kv(&[&path], input);
    assert_eq!((code, out.as_str()), (0, ""));
    // 다음 실행이 같은 파일에서 되찾는다
    let (code, out, _) = run_kv(&[&path], "get name\nget tab\nlist\n");
    assert_eq!(code, 0);
    assert_eq!(out, "보리\na\tb\nname\t보리\ntab\ta\\tb\n");
    fs::remove_file(&path).unwrap();
}

#[test]
fn corrupt_store_stops_before_any_command() {
    let path = fresh("corrupt");
    fs::write(&path, "a\t1\nb 2\n").unwrap();
    let args = [path.clone()];
    let mut out = Vec::new();
    let mut err = Vec::new();
    let stdin = "get a\nset c 3\n".as_bytes();
    let got = kv::run(&args, stdin, &mut out, &mut err);
    let Err(KvError::Corrupt(name, line, _)) = got else {
        panic!("Corrupt 가 아니다");
    };
    assert_eq!((name, line), (path.clone(), 2));
    // 답도 알림도 없고, 파일도 그대로다
    assert!(out.is_empty() && err.is_empty());
    assert_eq!(fs::read_to_string(&path).unwrap(), "a\t1\nb 2\n");
    fs::remove_file(&path).unwrap();
}

#[test]
fn broken_input_keeps_what_was_done() {
    // 셋째 줄이 글이 아니다
    let path = fresh("badline");
    let args = [path.clone()];
    let stdin = &b"set a 1\nget a\n\xff\nset b 2\n"[..];
    let mut out = Vec::new();
    let mut err = Vec::new();
    let got = kv::run(&args, stdin, &mut out, &mut err);
    assert!(matches!(got, Err(KvError::Io(_))));
    // 그 앞 줄의 답은 이미 쓰였고, 파일에도 들어갔다
    assert_eq!(out, b"1\n");
    assert_eq!(fs::read_to_string(&path).unwrap(), "a\t1\n");
    fs::remove_file(&path).unwrap();
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
    let stdin = "set a 1\nget a\n".as_bytes();
    let got = kv::run(&[], stdin, &mut Broken, &mut sink);
    assert_eq!(got.unwrap_err().to_string(), "닫힌 출력");
    // 찍을 것이 없는 명령뿐이면 쓰지 않으므로 실패도 없다
    let stdin = "set a 1\ndel a\n\n".as_bytes();
    let got = kv::run(&[], stdin, &mut Broken, &mut sink);
    assert_eq!(got.unwrap(), 0);
    // 알림을 쓰지 못해도 Err 로 돌아온다
    let got =
        kv::run(&[], "get a\n".as_bytes(), &mut sink, &mut Broken);
    assert_eq!(got.unwrap_err().to_string(), "닫힌 출력");
    assert!(sink.is_empty());
}

#[test]
fn scripts_are_answered_in_the_order_given() {
    let fruit = format!("{ROOT}/data/fruit.txt");
    let color = format!("{ROOT}/data/color.txt");
    let city = format!("{ROOT}/data/city.txt");
    let path = fresh("jobs");
    // 표준 입력에 준 줄은 읽지 않는다
    let (code, out, err) =
        run_kv(&[&path, &fruit, &color, &city], "set x 1\n");
    assert_eq!(code, 1);
    assert_eq!(out, "사과\n자두\n파랑\n다홍\n서울\n부산\n");
    let want = format!(
        "kv: {fruit} 5번째 줄: 없는 키 fruit.pear\n\
         kv: {city} 3번째 줄: 없는 키 city.busan\n"
    );
    assert_eq!(err, want);
    // 세 일꾼이 둔 것이 한 파일에 키의 순서로 있다
    let text = fs::read_to_string(&path).unwrap();
    assert_eq!(
        text,
        "city.busan\t부산\ncity.seoul\t서울\n\
         color.blue\t파랑\ncolor.red\t다홍\n\
         fruit.apple\t사과\nfruit.plum\t자두\n"
    );
    // 명령 파일의 차례를 바꿔 주면 답의 차례가 따라 바뀐다
    let path = fresh("jobs");
    let (_, out, _) = run_kv(&[&path, &city, &fruit], "");
    assert_eq!(out, "서울\n부산\n사과\n자두\n");
    fs::remove_file(&path).unwrap();
}

#[test]
fn unreadable_script_stops_before_any_command() {
    let fruit = format!("{ROOT}/data/fruit.txt");
    let none = format!("{ROOT}/data/none.txt");
    let path = fresh("noscript");
    let args = [path.clone(), fruit, none.clone()];
    let mut out = Vec::new();
    let mut err = Vec::new();
    let got = kv::run(&args, "".as_bytes(), &mut out, &mut err);
    let Err(KvError::File(name, _)) = got else {
        panic!("File 이 아니다");
    };
    assert_eq!(name, none);
    // 앞의 명령 파일도 돌지 않아서 저장소 파일이 생기지 않았다
    assert!(out.is_empty() && fs::read_to_string(&path).is_err());
}
