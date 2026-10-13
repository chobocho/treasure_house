use std::fmt::Display;

fn boxed<T: Display>(value: T) -> Box<dyn Display> {
    Box::new(value)
}

fn main() {
    let b = boxed(42);
    println!("{b}");
}
//@ expect: E0310
