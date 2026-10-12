// 실행 파일을 띄우지 않고, 인자를 손으로 만들어 run 을 부른다.
use shout::run;

fn args(words: &[&str]) -> Vec<String> {
    words.iter().map(|w| w.to_string()).collect()
}

#[test]
fn joins_and_shouts() {
    let text = run(&args(&["hello", "rust"]));
    assert_eq!(text, Ok(String::from("HELLO RUST!")));
}

#[test]
fn no_args_is_usage() {
    let usage = run(&args(&[])).unwrap_err();
    assert!(usage.starts_with("쓰는 법"));
}
