struct Point<T> {
    x: T,
    y: T,
}

fn main() {
    let p = Point { x: 1, y: 2.5 };
    println!("{} {}", p.x, p.y);
}
//@ expect: E0308
