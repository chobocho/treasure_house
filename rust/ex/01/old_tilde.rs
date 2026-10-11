// 옛 Rust 에서 ~ 는 포인터 종류 하나를 가리키는 기호였다.
fn main() {
    let s = ~"hello";
    println!("{}", s);
}
//@ expect: error
