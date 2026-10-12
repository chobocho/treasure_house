use std::any::Any;
use std::fmt::Debug;

// Shape 의 상위 트레이트는 Debug 와 Any 다.
trait Shape: Debug + Any {
    fn area(&self) -> f64;
}

#[derive(Debug)]
struct Circle(f64);
#[derive(Debug)]
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

// Shape 를 모르는 함수 — Debug 인 것이면 받는다.
fn log(what: &dyn Debug) -> String {
    format!("기록 {what:?}")
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> =
        vec![Box::new(Circle(1.0)), Box::new(Square(2.0))];
    for s in &shapes {
        let shape: &dyn Shape = s.as_ref();
        // &dyn Shape 를 &dyn Debug 로, &dyn Any 로 바꾼다.
        let debug: &dyn Debug = shape;
        let any: &dyn Any = shape;
        let radius = any.downcast_ref::<Circle>().map(|c| c.0);
        println!("{} / {} / {radius:?}", log(debug), shape.area());
    }
}
