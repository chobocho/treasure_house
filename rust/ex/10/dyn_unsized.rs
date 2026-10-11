trait Shape {
    fn area(&self) -> f64;
}

struct Circle(f64);

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
}

fn main() {
    let s: dyn Shape = Circle(1.0);
    println!("{}", s.area());
}
//@ expect: E0277
