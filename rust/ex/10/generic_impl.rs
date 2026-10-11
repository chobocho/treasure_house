struct Point<T> {
    x: T,
    y: T,
}

// 모든 T 에 대해.
impl<T> Point<T> {
    fn new(x: T, y: T) -> Self {
        Point { x, y }
    }

    fn x(&self) -> &T {
        &self.x
    }
}

// f64 일 때만 있는 메서드.
impl Point<f64> {
    fn distance(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}

fn main() {
    let a = Point::new(3, 4);
    let b = Point::new(3.0, 4.0);
    println!("{} {} {}", a.x(), a.y, b.distance());
}
