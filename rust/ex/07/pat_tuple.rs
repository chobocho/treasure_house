fn quadrant(point: (i32, i32)) -> &'static str {
    match point {
        (0, 0) => "원점",
        (x, y) if x > 0 && y > 0 => "1사분면",
        (x, _) if x < 0 => "왼쪽",
        (_, _) => "그 밖",
    }
}

fn main() {
    println!("{} {}", quadrant((0, 0)), quadrant((2, 3)));
    println!("{} {}", quadrant((-1, 9)), quadrant((4, -4)));
}
