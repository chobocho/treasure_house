use std::mem::size_of;

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
    // 보통 참조는 주소 하나. dyn 참조는 주소 + 메서드 표의 주소.
    println!("{}", size_of::<&Circle>());
    println!("{}", size_of::<&dyn Shape>());
    println!("{}", size_of::<Box<dyn Shape>>());
    let s: &dyn Shape = &Circle(1.0);
    println!("{}", s.area());
}
