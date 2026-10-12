// run 을 프로세스 없이 부른다. 표준 입력 자리에는 &[u8] 를,
// 표준 출력과 표준 오류 자리에는 Vec<u8> 를 넣는다
fn run_wc(args: &[&str], stdin: &str) -> (u8, String, String) {
    let args: Vec<String> =
        args.iter().map(|a| a.to_string()).collect();
    let mut out = Vec::new();
    let mut err = Vec::new();
    let code =
        wc::run(&args, stdin.as_bytes(), &mut out, &mut err).unwrap();
    let out = String::from_utf8(out).unwrap();
    let err = String::from_utf8(err).unwrap();
    (code, out, err)
}

#[test]
fn stdin_row_has_no_name() {
    let (code, out, err) = run_wc(&[], "a b\nc");
    assert_eq!((code, out.as_str()), (0, "    1     3     5\n"));
    assert_eq!(err, "");
}

#[test]
fn flags_pick_columns() {
    let (code, out, _) = run_wc(&["-m", "-l"], "가 나\n");
    assert_eq!((code, out.as_str()), (0, "    1     4\n"));
}

#[test]
fn unknown_flag_writes_usage_to_err_only() {
    let (code, out, err) = run_wc(&["-x", "data/sky.txt"], "");
    assert_eq!((code, out.as_str()), (2, ""));
    assert_eq!(err, format!("wc: 모르는 옵션 -x\n{}\n", wc::USAGE));
}

#[test]
fn missing_file_does_not_stop_the_rest() {
    let files = ["data/todo.txt", "data/none.txt", "data/sky.txt"];
    let (code, out, err) = run_wc(&files, "");
    assert_eq!(code, 1);
    let want = [
        "    1     3    14 data/todo.txt\n",
        "    2     4    28 data/sky.txt\n",
        "    3     7    42 total\n",
    ]
    .concat();
    assert_eq!(out, want);
    // 운영 체제가 주는 까닭은 견주지 않는다
    assert!(err.starts_with("wc: data/none.txt: "));
}

#[test]
fn byte_string_as_stdin() {
    let mut out = Vec::new();
    let mut err = Vec::new();
    let code = wc::run(&[], b"a b\n", &mut out, &mut err).unwrap();
    assert_eq!(code, 0);
    assert_eq!(out, b"    1     2     4\n");
}
