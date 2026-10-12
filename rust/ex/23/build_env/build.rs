use std::fs;

// 패키지보다 먼저 컴파일되어 도는 프로그램이다.
fn main() {
    let text = fs::read_to_string("colors.txt").unwrap();
    let count = text.lines().count();
    println!("build.rs 가 {count}줄을 셌다");
    // cargo:: 로 시작하는 줄은 Cargo 가 읽는다.
    println!("cargo::rustc-env=COLOR_COUNT={count}");
    println!("cargo::rerun-if-changed=colors.txt");
}
