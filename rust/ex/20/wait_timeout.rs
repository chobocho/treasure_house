use std::sync::{Condvar, Mutex};
use std::time::Duration;

fn main() {
    let ready = Mutex::new(false);
    let changed = Condvar::new();
    let limit = Duration::from_millis(10);

    // 조건을 바꿔 줄 스레드가 없다.
    let guard = ready.lock().unwrap();
    let (guard, result) = changed
        .wait_timeout_while(guard, limit, |ready| !*ready)
        .unwrap();
    println!("조건: {}", *guard);
    println!("한도가 지나서 돌아왔나: {}", result.timed_out());
    drop(guard);

    // 조건이 이미 참이면 기다리지 않는다.
    *ready.lock().unwrap() = true;
    let guard = ready.lock().unwrap();
    let (guard, result) = changed
        .wait_timeout_while(guard, limit, |ready| !*ready)
        .unwrap();
    println!("조건: {}", *guard);
    println!("한도가 지나서 돌아왔나: {}", result.timed_out());
}
