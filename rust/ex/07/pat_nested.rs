enum Shape {
    Circle { center: (i32, i32), r: u32 },
    Line((i32, i32), (i32, i32)),
}

fn touches_origin(s: &Shape) -> bool {
    match s {
        // 열거형 안의 구조체 안의 튜플까지 한 번에 풀어 헤친다.
        Shape::Circle { center: (0, 0), .. } => true,
        Shape::Circle { .. } => false,
        Shape::Line((0, 0), _) | Shape::Line(_, (0, 0)) => true,
        Shape::Line(..) => false,
    }
}

fn main() {
    let shapes = [
        Shape::Circle {
            center: (0, 0),
            r: 2,
        },
        Shape::Circle {
            center: (5, 5),
            r: 1,
        },
        Shape::Line((1, 1), (0, 0)),
        Shape::Line((1, 1), (2, 2)),
    ];
    for s in &shapes {
        print!("{} ", touches_origin(s));
    }
    println!();
    if let Shape::Circle { r, .. } = &shapes[0] {
        println!("반지름 {r}");
    }
}
