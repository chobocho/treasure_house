use std::sync::OnceLock;
use std::thread;

static CONFIG: OnceLock<String> = OnceLock::new();

fn config() -> &'static str {
    // 처음 부른 스레드가 한 번만 만든다. 나머지는 그 값을 받는다.
    CONFIG.get_or_init(|| {
        println!("(설정을 읽는다)");
        String::from("port=8080")
    })
}

fn main() {
    let handles: Vec<_> =
        (0..3).map(|_| thread::spawn(|| config().len())).collect();
    for h in handles {
        println!("{}", h.join().unwrap());
    }
}
