use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    // Arc 로 함께 갖고, Mutex 로 한 번에 하나만 고친다.
    let counter = Arc::new(Mutex::new(0));
    let mut handles = Vec::new();

    for _ in 0..8 {
        let counter = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                *counter.lock().unwrap() += 1;
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    println!("{}", *counter.lock().unwrap());
}
