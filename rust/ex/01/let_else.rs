fn port(s: &str) -> u16 {
    // 맞지 않으면 else 로 빠져나가고, 맞으면 n 을 아래에서 쓴다.
    let Ok(n) = s.parse::<u16>() else {
        return 8080;
    };
    n
}

fn main() {
    println!("{} {}", port("443"), port("https"));
}
