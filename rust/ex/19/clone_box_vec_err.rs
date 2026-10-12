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

// 같은 구현을 Box 대신 Vec 에 쓴다.
impl Clone for Vec<Box<dyn Shape>> {
    fn clone(&self) -> Self {
        self.iter().map(|s| s.clone_box()).collect()
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
//@ expect: E0117
