use std::fmt::Display;

// T: 'static — "T 안에 잠깐 빌린 참조가 들어 있지 않다".
fn show<T: Display + 'static>(value: T) {
    println!("{value}");
}

fn main() {
    show(42); // 정수 — 참조가 없다
    show(String::from("가진 문자열")); // 스스로 가진 값
    show("리터럴"); // &'static str
}
