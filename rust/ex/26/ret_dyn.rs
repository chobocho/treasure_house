use std::fmt::Display;

fn answer() -> impl Display {
    42
}

fn main() {
    println!("{}", answer().to_string());
}
