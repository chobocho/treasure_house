#[derive(Debug)]
struct Config {
    host: String,
    port: u16,
}

// 0 이나 빈 문자열이 알맞은 기본값이 아닐 때는 직접 구현한다.
impl Default for Config {
    fn default() -> Self {
        Config {
            host: String::from("localhost"),
            port: 8080,
        }
    }
}

fn main() {
    println!("{:?}", Config::default());
    let c = Config {
        port: 443,
        ..Default::default()
    };
    println!("{}:{}", c.host, c.port);
}
