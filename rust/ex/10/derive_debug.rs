#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

struct Raw {
    x: i32,
}

fn main() {
    println!("{:?}", Point { x: 1, y: 2 });
    println!("{:?}", Raw { x: 1 });
}
//@ expect: E0277
