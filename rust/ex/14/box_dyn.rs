trait Shape {
    fn area(&self) -> f64;
}

struct Circle(f64);
struct Square(f64);

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
}

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

fn main() {
    // 크기가 다른 타입들을 Box 에 넣으면 한 벡터에 담을 수 있다.
    let shapes: Vec<Box<dyn Shape>> =
        vec![Box::new(Circle(1.0)), Box::new(Square(2.0))];
    for s in &shapes {
        println!("{}", s.area());
    }
}
