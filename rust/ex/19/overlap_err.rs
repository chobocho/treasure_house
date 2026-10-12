use std::fmt::Display;

trait Describe {
    fn describe(&self) -> String;
}

// Display 인 모든 타입에
impl<T: Display> Describe for T {
    fn describe(&self) -> String {
        format!("값 {self}")
    }
}

// String 만은 따옴표를 둘러 주고 싶다.
impl Describe for String {
    fn describe(&self) -> String {
        format!("글 \"{self}\"")
    }
}

fn main() {
    println!("{}", 42.describe());
    println!("{}", String::from("hi").describe());
}
//@ expect: E0119
