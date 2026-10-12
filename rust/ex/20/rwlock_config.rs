use std::mem;
use std::sync::{Arc, RwLock};
use std::thread;

struct Config {
    version: u32,
    greeting: &'static str,
}

// 읽는 스레드 셋을 돌려, 각자 본 것을 만든 순서대로 모은다.
fn read_all(config: &Arc<RwLock<Config>>) -> Vec<String> {
    let readers: Vec<_> = (0..3)
        .map(|_| {
            let config = Arc::clone(config);
            thread::spawn(move || {
                let now = config.read().unwrap(); // 읽는 잠금
                format!("v{} {}", now.version, now.greeting)
            })
        })
        .collect();
    readers.into_iter().map(|r| r.join().unwrap()).collect()
}

fn main() {
    let first = Config {
        version: 1,
        greeting: "안녕",
    };
    let config = Arc::new(RwLock::new(first));
    println!("{:?}", read_all(&config));

    // 새 값은 잠그기 전에 다 만든다.
    let next = Config {
        version: 2,
        greeting: "반갑다",
    };
    // 쓰는 잠금은 통째로 바꿔 넣는 그 문에서만 쥔다.
    let old = mem::replace(&mut *config.write().unwrap(), next);
    println!("물러난 값: v{} {}", old.version, old.greeting);

    println!("{:?}", read_all(&config));
}
