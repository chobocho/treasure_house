struct Vec2 {
    x: f64,
    y: f64,
}

fn main() {
    let a = Vec2 { x: 1.0, y: 2.0 };
    let b = Vec2 { x: 0.5, y: -1.0 };
    let c = a + b;
    println!("{} {}", c.x, c.y);
}
//@ expect: E0369
