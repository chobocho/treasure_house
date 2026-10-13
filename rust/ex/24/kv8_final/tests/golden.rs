use std::fs;

// 패키지 뿌리 — 컴파일할 때 정해지는 글
const ROOT: &str = env!("CARGO_MANIFEST_DIR");

#[test]
fn transcript_matches_golden() {
    // 명령 한 벌과, 그 명령들에 기대하는 두 출력
    let input = fs::read(format!("{ROOT}/data/session.txt")).unwrap();
    let want_out =
        fs::read_to_string(format!("{ROOT}/tests/golden/session.out"))
            .unwrap();
    let want_err =
        fs::read_to_string(format!("{ROOT}/tests/golden/session.err"))
            .unwrap();
    let mut out = Vec::new();
    let mut err = Vec::new();
    let code = kv::run(&[], &input[..], &mut out, &mut err).unwrap();
    assert_eq!(code, 1);
    assert_eq!(String::from_utf8(out).unwrap(), want_out);
    assert_eq!(String::from_utf8(err).unwrap(), want_err);
}
