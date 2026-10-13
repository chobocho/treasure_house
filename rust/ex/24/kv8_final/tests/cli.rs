use std::fs;
use std::io::Write;
use std::process::{Command, Stdio};

// Cargo 가 넣어 주는 값 — 이 패키지의 실행 파일 kv 의 경로
const EXE: &str = env!("CARGO_BIN_EXE_kv");

const ROOT: &str = env!("CARGO_MANIFEST_DIR");

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

// 시험마다 제 이름의 저장소 파일을 쓴다
fn fresh(name: &str) -> String {
    let dir = format!("{ROOT}/target/kv-test");
    fs::create_dir_all(&dir).unwrap();
    let path = format!("{dir}/cli-{name}.kv");
    let _ = fs::remove_file(&path);
    path
}

#[test]
fn second_process_finds_what_the_first_set() {
    let path = fresh("two");
    let input = "set name 보리\nget name\n".as_bytes();
    let (code, out, err) = launch(&[&path], input);
    assert_eq!(
        (code, out.as_str(), err.as_str()),
        (Some(0), "보리\n", "")
    );
    // 첫 프로세스는 끝났다. 둘째가 파일에서 되찾는다
    let (code, out, err) = launch(&[&path], b"get name\nget age\n");
    assert_eq!((code, out.as_str()), (Some(1), "보리\n"));
    assert_eq!(err, "kv: 2번째 줄: 없는 키 age\n");
    fs::remove_file(&path).unwrap();
}

#[test]
fn corrupt_store_exits_two_with_the_line_number() {
    let path = fresh("corrupt");
    fs::write(&path, "a\t1\nb 2\n").unwrap();
    let (code, out, err) = launch(&[&path], b"get a\n");
    assert_eq!((code, out.as_str()), (Some(2), ""));
    assert_eq!(err, format!("kv: {path} 2번째 줄: 탭이 없다\n"));
    fs::remove_file(&path).unwrap();
}

#[test]
fn usage_and_unreadable_stdin_exit_two() {
    let (code, out, err) = launch(&["--help"], b"");
    assert_eq!((code, out.as_str()), (Some(2), ""));
    assert!(err.starts_with("쓰는 법: kv"));
    let (code, out, err) = launch(&[], b"set a 1\nget a\n\xff\n");
    assert_eq!((code, out.as_str()), (Some(2), "1\n"));
    // 까닭은 표준 라이브러리가 정하는 글이라 앞머리만 본다
    assert!(err.starts_with("kv: "));
    assert_eq!(err.lines().count(), 1);
}

#[test]
fn workers_exit_one_after_any_notice() {
    let path = fresh("jobs");
    let color = format!("{ROOT}/data/color.txt");
    let city = format!("{ROOT}/data/city.txt");
    // color.txt 에는 알림을 낼 줄이 없고 city.txt 에는 있다
    let (code, out, err) = launch(&[&path, &color], b"");
    assert_eq!(
        (code, out.as_str(), err.as_str()),
        (Some(0), "파랑\n다홍\n", "")
    );
    let (code, out, _) = launch(&[&path, &color, &city], b"");
    assert_eq!(
        (code, out.as_str()),
        (Some(1), "파랑\n다홍\n서울\n부산\n")
    );
    fs::remove_file(&path).unwrap();
}
