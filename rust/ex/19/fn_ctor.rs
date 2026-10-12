struct Meters(f64);

enum Shape {
    Circle(f64),
    Square(f64),
}

fn describe(shape: &Shape) -> String {
    match shape {
        Shape::Circle(r) => format!("반지름 {r} 인 원"),
        Shape::Square(side) => format!("한 변 {side} 인 정사각형"),
    }
}

fn main() {
    let raw = [1.5, 2.0];
    // 튜플 구조체의 이름은 f64 를 받아 Meters 를 돌려주는 함수다.
    let lengths: Vec<Meters> =
        raw.iter().copied().map(Meters).collect();
    let total: f64 = lengths.iter().map(|Meters(m)| m).sum();
    println!("{total}");
    // 열거형의 변형도, Some 도 마찬가지다.
    let mut shapes: Vec<Shape> =
        raw.iter().copied().map(Shape::Circle).collect();
    let maybe: Vec<Option<f64>> =
        raw.iter().copied().map(Some).collect();
    println!("{maybe:?}");
    // 타입을 적어 변수에 담을 수도 있다.
    let make: fn(f64) -> Shape = Shape::Square;
    shapes.push(make(3.0));
    for shape in &shapes {
        println!("{}", describe(shape));
    }
}
