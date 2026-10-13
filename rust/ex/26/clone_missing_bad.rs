struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let a = Point { x: 1, y: 2 };
    let b = a.clone();
    println!("{} {}", a.x + b.x, a.y + b.y);
}
//@ expect: E0599
