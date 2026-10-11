struct Point<T> {
    x: T,
    y: T,
}

impl Point<f64> {
    fn distance(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}

fn main() {
    let a = Point { x: 3, y: 4 };
    println!("{}", a.distance());
}
//@ expect: E0599
