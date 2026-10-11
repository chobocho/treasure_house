struct Point {
    x: i32,
    y: i32,
}

fn describe(p: &Point) -> String {
    match p {
        // 필드 값을 견주면서, 나머지 필드는 이름으로 꺼낸다.
        Point { x: 0, y: 0 } => String::from("원점"),
        Point { x: 0, y } => format!("y축 위 (y={y})"),
        Point { x, y: 0 } => format!("x축 위 (x={x})"),
        Point { x, y } => format!("({x}, {y})"),
    }
}

fn main() {
    for (x, y) in [(0, 0), (0, 5), (3, 0), (3, 5)] {
        println!("{}", describe(&Point { x, y }));
    }
}
