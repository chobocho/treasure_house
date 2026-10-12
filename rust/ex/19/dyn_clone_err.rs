// 복제할 수 있어야 한다고 상위 트레이트로 적었다.
trait Shape: Clone {
    fn area(&self) -> f64;
}

#[derive(Clone)]
struct Circle(f64);

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![Box::new(Circle(1.0))];
    let copy = shapes.clone();
    println!("{}", copy[0].area());
}
//@ expect: E0038
