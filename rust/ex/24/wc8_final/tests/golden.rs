use std::fs;

// 기준 파일의 경로 — 컴파일할 때 패키지 뿌리 뒤에 이어 만든다
const GOLDEN: &str =
    concat!(env!("CARGO_MANIFEST_DIR"), "/tests/golden/all.txt");

#[test]
fn all_columns_match_golden() {
    let args: Vec<String> =
        ["-lwmc", "data/sky.txt", "data/todo.txt", "data/empty.txt"]
            .iter()
            .map(|a| a.to_string())
            .collect();
    let mut out = Vec::new();
    let mut err = Vec::new();
    let code =
        wc::run(&args, "".as_bytes(), &mut out, &mut err).unwrap();
    assert_eq!(code, 0);
    assert!(err.is_empty());
    let want = fs::read_to_string(GOLDEN).unwrap();
    assert_eq!(String::from_utf8(out).unwrap(), want);
}
