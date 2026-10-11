trait Shape {
    fn area(&self) -> f64;
}
struct Sq(f64);
impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

fn main() {
    // 옛 표기: 트레이트 이름을 타입처럼 그대로 쓴다.
    let s: Box<Shape> = Box::new(Sq(3.0));
    println!("{}", s.area());
}
//@ edition: 2021
//@ expect: E0782
