use std::sync::{Mutex, TryLockError};
use std::thread;

fn peek(m: &Mutex<u32>) -> String {
    match m.try_lock() {
        Ok(guard) => format!("잠갔다, 값 {}", *guard),
        Err(TryLockError::WouldBlock) => String::from("누가 쥐고 있다"),
        Err(TryLockError::Poisoned(e)) => {
            format!("독이 들었다, 값 {}", *e.into_inner())
        }
    }
}

fn main() {
    let counter = Mutex::new(1);

    let guard = counter.lock().unwrap(); // 이 스레드가 쥐고 있다
    println!("{}", peek(&counter));
    drop(guard);
    println!("{}", peek(&counter));

    thread::scope(|s| {
        let worker = s.spawn(|| {
            let mut guard = counter.lock().unwrap();
            *guard += 1;
            panic!("쥔 채로 패닉");
        });
        let _ = worker.join();
    });
    println!("{}", peek(&counter));
}
