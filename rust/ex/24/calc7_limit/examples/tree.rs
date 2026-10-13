use std::env;

// 인자마다 그 글과, parse 가 돌려준 것을 {:?} 로 찍는다
fn main() {
    for line in env::args().skip(1) {
        let tree = calc::tokenize(&line).and_then(|t| calc::parse(&t));
        println!("{line:?}");
        println!("  {tree:?}");
    }
}
