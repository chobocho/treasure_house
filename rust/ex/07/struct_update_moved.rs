struct Config {
    host: String,
    port: u16,
}

fn main() {
    let base = Config {
        host: String::from("localhost"),
        port: 80,
    };
    let secure = Config { port: 443, ..base };
    println!("{} {}", secure.host, secure.port);
    println!("{}", base.port); // 복사되는 필드는 아직 쓸 수 있다
    println!("{}", base.host); // String 은 secure 로 옮겨 갔다
}
//@ expect: E0382
