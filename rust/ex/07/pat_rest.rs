struct Config {
    host: String,
    port: u16,
    verbose: bool,
    retries: u32,
}

fn main() {
    let c = Config {
        host: String::from("localhost"),
        port: 8080,
        verbose: true,
        retries: 3,
    };
    // .. — 나머지 필드는 상관없다.
    let Config { host, port, .. } = &c;
    println!("{host}:{port}");
    println!("{} {}", c.verbose, c.retries);

    let numbers = (1, 2, 3, 4, 5);
    let (first, .., last) = numbers; // 가운데는 건너뛴다
    println!("{first} {last}");
}
