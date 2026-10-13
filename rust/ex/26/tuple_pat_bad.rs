struct Circle {
    r: f64,
}

fn main() {
    let c = Circle { r: 2.0 };
    let Circle(r) = c;
    println!("{}", 3.0 * r * r);
}
//@ expect: E0532
