trait Shape {
    fn area(&self) -> f64;

    // 이 메서드는 크기를 아는 타입에만 있다 — dyn 에는 없다.
    fn area_times<N: Into<f64>>(&self, k: N) -> f64
    where
        Self: Sized,
    {
        self.area() * k.into()
    }
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
    println!("{}", Square(2.0).area_times(3));
    let shapes: Vec<Box<dyn Shape>> =
        vec![Box::new(Circle(1.0)), Box::new(Square(2.0))];
    for s in &shapes {
        println!("{}", s.area_times(3));
    }
}
//@ expect: error
