trait Shape {
    fn area(&self) -> f64;

    // 기본 구현 — 구현하는 쪽이 따로 쓰지 않으면 이것을 쓴다.
    fn describe(&self) -> String {
        format!("넓이 {:.1} 인 도형", self.area())
    }
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

    // 기본 구현을 덮어쓴다.
    fn describe(&self) -> String {
        format!("반지름 {} 인 원", self.0)
    }
}

fn main() {
    println!("{}", Square(2.0).describe());
    println!("{}", Circle(1.0).describe());
}
