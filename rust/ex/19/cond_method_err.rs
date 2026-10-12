use std::fmt::Display;

struct Labeled<T> {
    label: &'static str,
    value: T,
}

impl<T> Labeled<T> {
    fn new(label: &'static str, value: T) -> Self {
        Labeled { label, value }
    }
}

impl<T: Display> Labeled<T> {
    fn line(&self) -> String {
        format!("{} = {}", self.label, self.value)
    }
}

fn main() {
    let tags = Labeled::new("tags", vec!["a", "b"]);
    println!("{}", tags.line());
}
//@ expect: E0599
