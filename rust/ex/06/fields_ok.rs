struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let mut p = Point { x: 1, y: 2 };
    let a = &mut p.x;
    let b = &mut p.y;
    // 서로 다른 필드라서 둘이 함께 살아 있어도 된다
    *a += 10;
    *b += 20;
    println!("{} {}", p.x, p.y);
}
