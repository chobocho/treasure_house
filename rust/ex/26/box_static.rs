use std::fmt::Display;

fn boxed<T: Display + 'static>(value: T) -> Box<dyn Display> {
    Box::new(value)
}

fn main() {
    let b = boxed(42);
    println!("{b}");
}
