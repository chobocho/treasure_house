trait Shape {
    fn area(&self) -> f64;
    fn name(&self) -> &str;
}

struct Circle(f64);
struct Square(f64);

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
    fn name(&self) -> &str {
        "원"
    }
}

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn name(&self) -> &str {
        "정사각형"
    }
}

fn main() {
    // dyn Shape — "Shape 을 구현한 무언가".
    // 실제 타입은 실행 중에 정해진다.
    let shapes: Vec<Box<dyn Shape>> =
        vec![Box::new(Circle(1.0)), Box::new(Square(2.0))];
    for s in &shapes {
        println!("{} {}", s.name(), s.area());
    }
}
