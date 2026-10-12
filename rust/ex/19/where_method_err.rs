use std::fmt::Display;

struct Labeled<T> {
    label: &'static str,
    value: T,
}

impl<T> Labeled<T> {
    fn line(&self) -> String
    where
        T: Display,
    {
        format!("{} = {}", self.label, self.value)
    }
}

fn main() {
    let tags = Labeled {
        label: "tags",
        value: vec!["a", "b"],
    };
    println!("{}", tags.line());
}
//@ expect: E0277
