use std::fmt::Display;

fn answer() -> dyn Display {
    42
}

fn main() {
    println!("{}", answer().to_string());
}
//@ expect: E0746,E0277
