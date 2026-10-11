use std::sync::Mutex;
use std::thread;

fn main() {
    let counter = Mutex::new(0);
    let mut handles = Vec::new();
    for _ in 0..2 {
        handles.push(thread::spawn(move || {
            *counter.lock().unwrap() += 1;
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
}
//@ expect: E0382
