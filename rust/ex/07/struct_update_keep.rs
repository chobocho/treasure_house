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
    // 옮겨 갈 필드는 복제해서 직접 적는다. ..base 가 가져가는 것은
    // 적지 않은 verbose 뿐이고, bool 은 복사된다.
    let secure = Config {
        host: base.host.clone(),
        port: 443,
        ..base
    };
    println!("{} {} {}", secure.host, secure.port, secure.verbose);
    println!("{} {} {}", base.host, base.port, base.verbose);
}
