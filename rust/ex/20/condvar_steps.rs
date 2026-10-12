use std::sync::{Condvar, Mutex};
use std::thread;

fn main() {
    let step = Mutex::new(0);
    let changed = Condvar::new();

    thread::scope(|s| {
        s.spawn(|| {
            for _ in 0..3 {
                *step.lock().unwrap() += 1;
                changed.notify_one(); // 바뀔 때마다 알린다
            }
        });

        // 3 이 되기를 기다린다. 그 전에 깨어나면 다시 잔다.
        let mut now = step.lock().unwrap();
        while *now < 3 {
            now = changed.wait(now).unwrap();
        }
        println!("깨어나서 본 값: {}", *now);
    });
}
