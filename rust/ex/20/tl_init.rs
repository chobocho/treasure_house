use std::cell::Cell;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::thread;

// 처음 값을 만드는 식이 몇 번 돌았는지 센다.
static INITS: AtomicUsize = AtomicUsize::new(0);

fn first_value() -> u32 {
    INITS.fetch_add(1, Ordering::SeqCst);
    100
}

thread_local! {
    static SLOT: Cell<u32> = Cell::new(first_value());
}

fn inits() -> usize {
    INITS.load(Ordering::SeqCst)
}

fn main() {
    println!("아무도 쓰기 전: {}", inits());

    // 이 스레드는 SLOT 을 여러 번 쓴다.
    let busy = thread::spawn(|| {
        SLOT.set(SLOT.get() + 1);
        SLOT.get()
    });
    println!("여러 번 쓴 스레드가 본 값: {}", busy.join().unwrap());
    println!("그 뒤: {}", inits());

    // 이 스레드는 SLOT 을 쓰지 않는다.
    thread::spawn(|| 0).join().unwrap();
    println!("쓰지 않은 스레드 뒤: {}", inits());

    println!("main 이 본 값: {}", SLOT.get());
    println!("main 이 쓴 뒤: {}", inits());
}
