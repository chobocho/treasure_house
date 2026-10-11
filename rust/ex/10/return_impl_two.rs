trait Shape {
    fn area(&self) -> f64;
}

struct Square(f64);
struct Circle(f64);

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
}

fn make(round: bool) -> impl Shape {
    if round { Circle(1.0) } else { Square(1.0) }
}

fn main() {
    println!("{}", make(true).area());
}
//@ expect: E0308
