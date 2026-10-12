use std::fmt::Display;

struct Labeled<T> {
    label: &'static str,
    value: T,
}

// 조건을 impl 블록 전체에 달았다.
impl<T: Display> Labeled<T> {
    fn new(label: &'static str, value: T) -> Self {
        Labeled { label, value }
    }
    fn line(&self) -> String {
        format!("{} = {}", self.label, self.value)
    }
}

fn main() {
    let port = Labeled::new("port", 8080);
    println!("{}", port.line());
    // Vec 은 Display 가 아니다.
    let tags = Labeled::new("tags", vec!["a", "b"]);
    println!("{}", tags.value.len());
}
//@ expect: E0277
