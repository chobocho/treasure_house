use std::env;

fn main() {
    // env! 는 컴파일할 때의 환경 변수를 문자열 리터럴로 바꿔 놓는다.
    println!("env!     {}", env!("CARGO_PKG_NAME"));
    println!("env!     {}", env!("CARGO_PKG_VERSION"));
    println!("env!     {}", env!("CARGO_MANIFEST_DIR"));
    // env::var 는 프로그램이 도는 지금의 환경 변수를 읽는다.
    println!("env::var {:?}", env::var("CARGO_PKG_VERSION"));
}
