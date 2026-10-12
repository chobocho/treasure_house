use std::process::Command;

// Cargo 가 넣어 주는 값 — 이 패키지의 실행 파일 wc 의 경로
const EXE: &str = env!("CARGO_BIN_EXE_wc");

#[test]
fn missing_file_exits_one() {
    let out = Command::new(EXE)
        .args(["-l", "data/todo.txt", "data/none.txt"])
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(1));
    let stdout = String::from_utf8(out.stdout).unwrap();
    assert_eq!(stdout, "    1 data/todo.txt\n    1 total\n");
    let stderr = String::from_utf8(out.stderr).unwrap();
    assert!(stderr.starts_with("wc: data/none.txt: "));
}

#[test]
fn unknown_flag_exits_two() {
    let out = Command::new(EXE).arg("-x").output().unwrap();
    assert_eq!(out.status.code(), Some(2));
    assert!(out.stdout.is_empty());
    let stderr = String::from_utf8(out.stderr).unwrap();
    assert_eq!(stderr, format!("wc: 모르는 옵션 -x\n{}\n", wc::USAGE));
}
