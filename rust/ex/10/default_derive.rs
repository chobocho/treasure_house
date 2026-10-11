#[derive(Debug, Default)]
struct Config {
    host: String,
    port: u16,
    verbose: bool,
}

fn main() {
    // 필드마다 그 타입의 기본값 — 빈 문자열, 0, false.
    println!("{:?}", Config::default());

    // 몇 개만 정하고 나머지는 기본값으로.
    let c = Config {
        port: 8080,
        ..Default::default()
    };
    println!("{c:?}");
    println!("{} {} {}", c.host.is_empty(), c.port, c.verbose);
}
