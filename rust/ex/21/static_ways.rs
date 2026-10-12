use std::sync::Mutex;
use std::sync::atomic::{AtomicU32, Ordering};

// 길 1: 원자 타입. mut 도 unsafe 도 없다.
static CALLS: AtomicU32 = AtomicU32::new(0);

// 길 2: Mutex. 수 하나가 아닌 값도 둘 수 있다.
static NAMES: Mutex<Vec<&str>> = Mutex::new(Vec::new());

// 길 3: static mut 을 그대로 두고, 참조 없이 날 포인터로만 닿는다.
static mut RAW_CALLS: u32 = 0;

fn record(name: &'static str) {
    CALLS.fetch_add(1, Ordering::Relaxed);
    NAMES.lock().unwrap().push(name);

    let p = &raw mut RAW_CALLS;
    // 안전: 스레드가 하나뿐이고, RAW_CALLS 를 가리키는 참조는 어디에도
    // 없다. p 는 프로그램 내내 살아 있는 static 을 가리킨다.
    unsafe { p.write(p.read() + 1) };
}

fn main() {
    record("a");
    record("b");
    println!("{}", CALLS.load(Ordering::Relaxed));
    println!("{:?}", NAMES.lock().unwrap());
    // 안전: record 와 같다. 값을 복사해 읽는다.
    let raw = unsafe { (&raw const RAW_CALLS).read() };
    println!("{raw}");
}
