use std::path::Path;

fn main() {
    let path = Path::new("notes/memo.txt");
    println!("{path}");
}
//@ expect: E0277
