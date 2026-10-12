use std::process::Command;

// Cargo 가 넣어 주는 값 — 이 패키지의 실행 파일 shout 의 경로.
const EXE: &str = env!("CARGO_BIN_EXE_shout");

#[test]
fn exe_is_under_target() {
    assert!(EXE.ends_with("/target/debug/shout"));
}

#[test]
fn prints_and_exits_zero() {
    let out =
        Command::new(EXE).args(["hello", "rust"]).output().unwrap();
    assert_eq!(out.status.code(), Some(0));
    assert_eq!(String::from_utf8(out.stdout).unwrap(), "HELLO RUST!\n");
    assert!(out.stderr.is_empty());
}

#[test]
fn no_args_exits_two() {
    let out = Command::new(EXE).output().unwrap();
    assert_eq!(out.status.code(), Some(2));
    assert!(out.stdout.is_empty());
    let usage = String::from_utf8(out.stderr).unwrap();
    assert_eq!(usage, "쓰는 법: shout <낱말>...\n");
}
