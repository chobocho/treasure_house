use std::thread;

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
    let shape: Box<dyn Shape + Send> = Box::new(Circle(1.0));
    // 넓이 계산을 다른 스레드에 맡긴다.
    let handle = thread::spawn(move || shape.area());
    println!("{}", handle.join().unwrap());
}
