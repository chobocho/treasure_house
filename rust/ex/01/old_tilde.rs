// 1.0 전에는 ~ 가 "힙에 놓인 소유 값" 을 뜻하는 기호였다.
fn main() {
    let s = ~"hello";
    println!("{}", s);
}
//@ expect: error
