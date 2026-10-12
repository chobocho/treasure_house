use std::fmt::Display;

trait Describe {
    fn describe(&self) -> String;
}

// 내가 만든 표시 — 붙인 타입만 포괄 구현을 받는다.
trait Plain: Display {}
impl Plain for i32 {}
impl Plain for f64 {}

impl<T: Plain> Describe for T {
    fn describe(&self) -> String {
        format!("값 {self}")
    }
}

impl Describe for String {
    fn describe(&self) -> String {
        format!("글 \"{self}\"")
    }
}

impl<T> Describe for Vec<T> {
    fn describe(&self) -> String {
        format!("{}칸짜리 벡터", self.len())
    }
}

fn main() {
    println!("{}", 42.describe());
    println!("{}", 2.5.describe());
    println!("{}", String::from("hi").describe());
    println!("{}", vec![1, 2, 3].describe());
}
