trait Shape {
    fn area(&self) -> f64;
    fn name(&self) -> String;
}

struct Circle {
    r: f64,
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.r * self.r
    }
}

fn main() {
    println!("{}", Circle { r: 1.0 }.area());
}
//@ expect: E0046
