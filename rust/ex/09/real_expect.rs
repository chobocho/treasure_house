fn main() {
    // 사람이 쓴 상수라 틀릴 수 없다 — 틀렸다면 그것은 버그다.
    let default_port: u16 = "8080".parse().expect("기본 포트는 숫자다");
    println!("{default_port}");

    // 바깥에서 온 값은 틀릴 수 있다 — 버그가 아니라 예상한 실패다.
    let input = "80a";
    match input.parse::<u16>() {
        Ok(p) => println!("{p}"),
        Err(e) => {
            println!("입력 `{input}` 을 포트로 읽을 수 없다: {e}")
        }
    }
}
