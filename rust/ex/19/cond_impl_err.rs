use std::fmt::Display;

trait Summary {
    fn summary(&self) -> String;
}

struct Labeled<T> {
    label: &'static str,
    value: T,
}

impl<T> Labeled<T> {
    fn new(label: &'static str, value: T) -> Self {
        Labeled { label, value }
    }
}

// T 가 Display 일 때만 Labeled<T> 가 Summary 다.
impl<T: Display> Summary for Labeled<T> {
    fn summary(&self) -> String {
        format!("{} = {}", self.label, self.value)
    }
}

fn report(item: &impl Summary) {
    println!("* {}", item.summary());
}

fn main() {
    let tags = Labeled::new("tags", vec!["a", "b"]);
    report(&tags);
}
//@ expect: E0277
