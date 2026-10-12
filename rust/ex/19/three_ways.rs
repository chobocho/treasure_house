trait Shape {
    fn area(&self) -> f64;
}

struct Circle(f64);
struct Rect(f64, f64);

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.0 * self.0
    }
}

impl Shape for Rect {
    fn area(&self) -> f64 {
        self.0 * self.1
    }
}

// 제네릭 — 타입은 컴파일할 때 정해진다.
fn area_generic<T: Shape>(s: &T) -> f64 {
    s.area()
}
// 빌린 트레이트 객체
fn area_ref(s: &dyn Shape) -> f64 {
    s.area()
}
// 가진 트레이트 객체
fn area_box(s: Box<dyn Shape>) -> f64 {
    s.area()
}

fn main() {
    let (c, r) = (Circle(1.0), Rect(2.0, 3.0));
    println!("{} {}", area_generic(&c), area_generic(&r));
    println!("{} {}", area_ref(&c), area_ref(&r));
    println!("{}", area_box(Box::new(Rect(2.0, 3.0))));
    println!("{} {}", size_of::<&Circle>(), size_of::<&Rect>());
    let fat = (size_of::<&dyn Shape>(), size_of::<Box<dyn Shape>>());
    println!("{fat:?}");
    // dyn 뒤에 있는 값의 크기는 값에 묻는다.
    let shapes: [&dyn Shape; 2] = [&c, &r];
    println!("{} {}", size_of_val(shapes[0]), size_of_val(shapes[1]));
}
