use std::fmt::Display;

struct Labeled<T> {
    label: &'static str,
    value: T,
}

// 어떤 T 에든 있는 것
impl<T> Labeled<T> {
    fn new(label: &'static str, value: T) -> Self {
        Labeled { label, value }
    }
    fn value(&self) -> &T {
        &self.value
    }
}

// T 가 Display 일 때만 있는 것
impl<T: Display> Labeled<T> {
    fn line(&self) -> String {
        format!("{} = {}", self.label, self.value)
    }
}

fn main() {
    let port = Labeled::new("port", 8080);
    println!("{}", port.line());
    let tags = Labeled::new("tags", vec!["a", "b"]);
    println!("{} {}", tags.label, tags.value().len());
}
