trait Shape {
    fn area(&self) -> f64;
    // 자기와 같은 것을 새 상자에 담아 돌려준다.
    fn clone_box(&self) -> Box<dyn Shape>;
}

#[derive(Clone)]
struct Circle(f64);
#[derive(Clone)]
struct Square(f64);

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
    fn clone_box(&self) -> Box<dyn Shape> {
        Box::new(self.clone())
    }
}

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn clone_box(&self) -> Box<dyn Shape> {
        Box::new(self.clone())
    }
}

// 상자에 Clone 을 직접 구현한다.
impl Clone for Box<dyn Shape> {
    fn clone(&self) -> Self {
        self.clone_box()
    }
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> =
        vec![Box::new(Circle(1.0)), Box::new(Square(2.0))];
    let copy = shapes.clone();
    drop(shapes);
    for s in &copy {
        println!("{}", s.area());
    }
}
