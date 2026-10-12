trait Shape {
    fn name(&self) -> String;
    fn area(&self) -> f64;

    // 기본 구현 — 구현마다 다른 name 과 area 를 부른다.
    fn label(&self) -> String {
        format!("{} {:.1}", self.name(), self.area())
    }
}

struct Circle(f64);
struct Square(f64);

impl Shape for Circle {
    fn name(&self) -> String {
        String::from("원")
    }
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
}

impl Shape for Square {
    fn name(&self) -> String {
        String::from("정사각형")
    }
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    // 기본 구현을 덮어쓴다.
    fn label(&self) -> String {
        format!("한 변 {} 인 {}", self.0, self.name())
    }
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle(1.0)),
        Box::new(Square(2.0)),
        Box::new(Circle(2.0)),
    ];
    for s in &shapes {
        println!("{}", s.label());
    }
}
