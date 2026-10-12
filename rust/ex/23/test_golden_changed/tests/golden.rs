use std::env;
use std::fs;

// 기준 파일의 경로 — 컴파일할 때 패키지 뿌리 뒤에 이어 만든다.
const GOLDEN: &str =
    concat!(env!("CARGO_MANIFEST_DIR"), "/tests/golden/report.txt");

#[test]
fn report_matches_golden() {
    let got = report::render(&[("apple", 3), ("kiwi", 12)]);
    // 이 변수를 주고 돌리면 지금의 출력으로 기준 파일을 새로 쓴다.
    if env::var("UPDATE_GOLDEN").is_ok() {
        fs::write(GOLDEN, &got).unwrap();
    }
    let want = fs::read_to_string(GOLDEN).unwrap();
    assert_eq!(got, want);
}
