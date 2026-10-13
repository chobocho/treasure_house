use std::fmt::Display;

// 무엇이든 받아, 찍을 수 있는 상자에 담아 돌려준다
fn boxed<'a, T: Display + 'a>(value: T) -> Box<dyn Display + 'a> {
    Box::new(value)
}

fn main() {
    let s = String::from("지역 변수");
    let b = boxed(&s);
    println!("{b}");
    println!("{}", boxed(42));
}
