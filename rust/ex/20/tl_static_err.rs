use std::cell::Cell;
use std::thread;

// 부른 횟수 — 어느 스레드에서나 보이는 static 에 둔다.
static CALLS: Cell<u32> = Cell::new(0);

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
//@ expect: E0277
