// 수명 표기는 값을 더 오래 살게 해 주지 않는다.
fn make<'a>() -> &'a String {
    let s = String::from("hello");
    &s
}

fn main() {
    println!("{}", make());
}
//@ expect: E0515
