use std::any::type_name;
use std::fmt::Display;

// ?Sized — T 의 크기를 몰라도 된다.
fn show<T: Display + ?Sized>(x: &T) -> String {
    format!("[{x}] T = {}", type_name::<T>())
}

fn main() {
    let n = 42;
    println!("{}", show(&n));
    let s: &str = "hello";
    println!("{}", show(s));
    let d: &dyn Display = &2.5;
    println!("{}", show(d));
}
