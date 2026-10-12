use std::cell::Cell;
use std::thread;

thread_local! {
    // 부른 횟수 — 스레드마다 하나씩 따로 생긴다.
    static CALLS: Cell<u32> = Cell::new(0);
}

fn call() -> u32 {
    CALLS.set(CALLS.get() + 1);
    CALLS.get()
}

fn main() {
    call();
    call();
    println!("main: {}", call());

    let a = thread::spawn(|| call()).join().unwrap();
    let b = thread::spawn(|| {
        call();
        call()
    });
    let b = b.join().unwrap();
    println!("새 스레드 둘: {a} {b}");
    println!("main 다시: {}", call());
}
