use std::fmt::Display;

trait Describe {
    fn describe(&self) -> String;
}

impl<T: Display> Describe for T {
    fn describe(&self) -> String {
        format!("값 {self}")
    }
}

// Vec 은 Display 가 아니다 — 겹칠 일이 없어 보인다.
impl<T> Describe for Vec<T> {
    fn describe(&self) -> String {
        format!("{}칸짜리 벡터", self.len())
    }
}

fn main() {
    println!("{}", 42.describe());
    println!("{}", vec![1, 2, 3].describe());
}
//@ expect: E0119
