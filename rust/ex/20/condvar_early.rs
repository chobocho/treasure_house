use std::sync::{Condvar, Mutex};
use std::thread;

fn main() {
    let ready = Mutex::new(false);
    let changed = Condvar::new();

    // 기다릴 쪽이 오기 전에 조건을 바꾸고 알린다.
    thread::scope(|s| {
        s.spawn(|| {
            *ready.lock().unwrap() = true;
            changed.notify_one(); // 잠든 스레드가 없다
        });
    });
    // 스코프가 끝났으니 알림은 이미 지나갔다.

    let mut waits = 0;
    let mut guard = ready.lock().unwrap();
    while !*guard {
        waits += 1;
        guard = changed.wait(guard).unwrap();
    }
    println!("조건: {}", *guard);
    println!("wait 를 부른 횟수: {waits}");
}
