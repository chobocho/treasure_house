fn main() {
    // 참조를 받아 그 일부를 돌려주는 클로저를 변수에 담는다.
    let first = |s: &str| s.split(' ').next().unwrap_or("");
    println!("{}", first("hello world"));
}
//@ expect: error
