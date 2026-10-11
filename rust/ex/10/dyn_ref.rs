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

// &dyn Shape — Box 없이 빌려서도 쓴다.
fn total(shapes: &[&dyn Shape]) -> f64 {
    let mut sum = 0.0;
    for s in shapes {
        sum += s.area();
    }
    sum
}

fn pick(round: bool) -> Box<dyn Shape> {
    // 2장에서 impl Shape 로는 못 하던 일.
    if round {
        Box::new(Circle(1.0))
    } else {
        Box::new(Square(1.0))
    }
}

fn main() {
    let c = Circle(1.0);
    let s = Square(2.0);
    println!("{:.2}", total(&[&c, &s]));
    println!("{} {}", pick(true).area(), pick(false).area());
}
