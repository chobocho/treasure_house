// 트레이트 — "이런 일을 할 수 있다" 는 약속.
trait Shape {
    fn area(&self) -> f64;
}

struct Circle {
    r: f64,
}

struct Rect {
    w: f64,
    h: f64,
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.r * self.r
    }
}

impl Shape for Rect {
    fn area(&self) -> f64 {
        self.w * self.h
    }
}

fn main() {
    let c = Circle { r: 1.0 };
    let r = Rect { w: 2.0, h: 3.0 };
    println!("{} {}", c.area(), r.area());
}
