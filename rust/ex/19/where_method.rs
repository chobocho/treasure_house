use std::fmt::Display;

struct Labeled<T> {
    label: &'static str,
    value: T,
}

impl<T> Labeled<T> {
    fn new(label: &'static str, value: T) -> Self {
        Labeled { label, value }
    }

    // 이 메서드에만 조건을 단다.
    fn line(&self) -> String
    where
        T: Display,
    {
        format!("{} = {}", self.label, self.value)
    }

    fn is_default(&self) -> bool
    where
        T: Default + PartialEq,
    {
        self.value == T::default()
    }
}

fn main() {
    let port = Labeled::new("port", 8080);
    println!("{} {}", port.line(), port.is_default());
    let tags: Labeled<Vec<&str>> = Labeled::new("tags", Vec::new());
    println!("{} {}", tags.label, tags.is_default());
}
