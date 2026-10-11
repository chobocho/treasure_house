use std::fmt::Display;

fn show<T: Display + 'static>(value: T) {
    println!("{value}");
}

fn main() {
    let s = String::from("지역 변수");
    show(&s); // &String — s 를 잠깐 빌린 참조다
}
//@ expect: E0597
