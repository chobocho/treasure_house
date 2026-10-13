use std::cell::Cell;

fn main() {
    let name = Cell::new(String::from("kim"));
    println!("{}", name.get());
}
//@ expect: E0599
