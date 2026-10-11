// derive 도 매크로다 — 이 한 줄이 impl Debug 블록을 써 준다.
#[derive(Debug, Clone, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let p = Point { x: 1, y: 2 };
    let q = p.clone();
    println!("{p:?} {}", p == q);
}
