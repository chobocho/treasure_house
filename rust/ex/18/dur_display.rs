use std::time::Duration;

fn main() {
    let movie = Duration::from_secs(7509);
    println!("{movie}");
}
//@ expect: E0277
