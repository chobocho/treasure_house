use std::fmt::Display;

fn show<T: Display>(x: &T) -> String {
    format!("[{x}]")
}

fn main() {
    let n = 42;
    println!("{}", show(&n));
    let s: &str = "hello";
    println!("{}", show(s));
}
//@ expect: E0277
