use std::sync::Arc;
use std::thread;

fn main() {
    // Arc 로 함께 갖기만 하고, 잠금 없이 고치려 한다.
    let counter = Arc::new(0);
    let mut handles = Vec::new();
    for _ in 0..8 {
        let counter = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            *counter += 1;
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    println!("{counter}");
}
//@ expect: E0594
