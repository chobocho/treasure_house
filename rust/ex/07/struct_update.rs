struct Config {
    host: String,
    port: u16,
    verbose: bool,
}

fn main() {
    let base = Config {
        host: String::from("localhost"),
        port: 80,
        verbose: false,
    };
    // 몇 개만 바꾸고 나머지는 base 에서 가져온다.
    let secure = Config { port: 443, ..base };
    println!("{} {} {}", secure.host, secure.port, secure.verbose);
}
