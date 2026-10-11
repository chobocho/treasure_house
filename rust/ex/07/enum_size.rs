use std::mem::size_of;

#[allow(dead_code)]
enum Shape {
    Circle(f64),
    Rect { w: f64, h: f64 },
    Dot,
}

fn main() {
    // 가장 큰 변형 + 어느 변형인지 적는 꼬리표.
    println!("{}", size_of::<Shape>());
    println!("{} {}", size_of::<u8>(), size_of::<Option<u8>>());
    // 참조는 0 일 수 없다 — None 을 0 으로 적으면 꼬리표가 필요 없다.
    println!("{} {}", size_of::<&u8>(), size_of::<Option<&u8>>());
}
