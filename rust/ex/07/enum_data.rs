// 변형마다 서로 다른 데이터를 가질 수 있다.
#[derive(Debug)]
enum Shape {
    Circle(f64),             // 튜플처럼
    Rect { w: f64, h: f64 }, // 구조체처럼
    Dot,                     // 데이터 없음
}

fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle(r) => 3.14 * r * r,
        Shape::Rect { w, h } => w * h,
        Shape::Dot => 0.0,
    }
}

fn main() {
    let shapes = [
        Shape::Circle(1.0),
        Shape::Rect { w: 2.0, h: 3.0 },
        Shape::Dot,
    ];
    for s in &shapes {
        println!("{s:?} → {}", area(s));
    }
}
