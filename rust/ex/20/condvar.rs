use std::sync::{Condvar, Mutex};
use std::thread;

fn main() {
    let ready = Mutex::new(false); // 조건
    let changed = Condvar::new(); // 조건이 바뀌었다고 알리는 종

    thread::scope(|s| {
        let mut guard = ready.lock().unwrap(); // main 이 먼저 잠근다
        println!("기다리기 전: {}", *guard);

        s.spawn(|| {
            *ready.lock().unwrap() = true; // 잠가야 바꿀 수 있다
            changed.notify_one();
        });

        while !*guard {
            // 열쇠를 내놓고 잠들었다가, 깨어나며 다시 쥔다.
            guard = changed.wait(guard).unwrap();
        }
        println!("깨어난 뒤: {}", *guard);
    });
}
