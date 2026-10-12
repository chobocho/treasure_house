use std::process::Command;

// Cargo 가 넣어 주는 값 — 이 패키지의 실행 파일 grep 의 경로
const EXE: &str = env!("CARGO_BIN_EXE_grep");

// 실행 파일을 띄워 종료 코드와 두 출력을 받는다
fn launch(args: &[&str]) -> (Option<i32>, String, String) {
    let out = Command::new(EXE).args(args).output().unwrap();
    let stdout = String::from_utf8(out.stdout).unwrap();
    let stderr = String::from_utf8(out.stderr).unwrap();
    (out.status.code(), stdout, stderr)
}

#[test]
fn selected_line_exits_zero() {
    let (code, out, err) = launch(&["-n", "milk", "data/todo.txt"]);
    assert_eq!((code, out.as_str()), (Some(0), "1:milk\n"));
    assert_eq!(err, "");
}

#[test]
fn no_selected_line_exits_one() {
    let (code, out, err) = launch(&["zig", "data/todo.txt"]);
    assert_eq!((code, out.as_str(), err.as_str()), (Some(1), "", ""));
}

#[test]
fn unreadable_file_exits_two() {
    let args = ["milk", "data/none.txt", "data/todo.txt"];
    let (code, out, err) = launch(&args);
    assert_eq!((code, out.as_str()), (Some(2), "data/todo.txt:milk\n"));
    assert!(err.starts_with("grep: data/none.txt: "));
}

#[test]
fn bad_invocation_exits_two() {
    let (code, out, err) = launch(&["-x", "milk"]);
    assert_eq!((code, out.as_str()), (Some(2), ""));
    assert_eq!(err, format!("grep: 모르는 옵션 -x\n{}\n", grep::USAGE));
}
