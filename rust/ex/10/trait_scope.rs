mod shapes {
    pub trait Shape {
        fn area(&self) -> f64;
    }

    pub struct Square(pub f64);

    impl Shape for Square {
        fn area(&self) -> f64 {
            self.0 * self.0
        }
    }
}

fn main() {
    let s = shapes::Square(2.0);
    println!("{}", s.area());
}
//@ expect: E0599
