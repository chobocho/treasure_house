trait Shape {
    fn area(&self) -> f64;
}

struct Square(f64);
struct Circle(f64);

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
}

// impl Shape — "Shape 를 구현한 타입이면 무엇이든".
fn print_area(shape: &impl Shape) {
    println!("{:.2}", shape.area());
}

// 위와 같은 뜻을 제네릭으로 풀어 쓴 모양.
fn print_area_generic<T: Shape>(shape: &T) {
    println!("{:.2}", shape.area());
}

fn main() {
    print_area(&Square(2.0));
    print_area_generic(&Circle(1.0));
}
