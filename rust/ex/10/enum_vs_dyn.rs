// 종류가 정해져 있으면 열거형으로도 된다 — Box 도 dyn 도 없다.
enum Shape {
    Circle(f64),
    Square(f64),
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle(r) => 3.14 * r * r,
            Shape::Square(s) => s * s,
        }
    }
}

fn main() {
    let shapes = vec![Shape::Circle(1.0), Shape::Square(2.0)];
    for s in &shapes {
        println!("{}", s.area());
    }
}
