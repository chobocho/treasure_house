fn main() {
    let config: Option<u16> = Some(8080);

    // match 로 쓰면 — 관심 없는 갈래도 써야 한다.
    match config {
        Some(port) => println!("포트 {port}"),
        None => {}
    }

    // if let — 한 가지 모양에만 관심이 있을 때.
    if let Some(port) = config {
        println!("포트 {port}");
    }
}
