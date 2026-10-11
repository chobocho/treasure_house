fn half(n: i32) -> Option<i32> {
    if n % 2 == 0 { Some(n / 2) } else { None }
}

fn main() {
    // and_then: Option 을 내는 일을 이어 붙인다.
    // 중간에 None 이 나오면 끝까지 None.
    println!("{:?}", Some(12).and_then(half).and_then(half));
    println!("{:?}", Some(10).and_then(half).and_then(half));
    // map 으로 하면 Option 이 겹친다.
    println!("{:?}", Some(12).map(half));
}
