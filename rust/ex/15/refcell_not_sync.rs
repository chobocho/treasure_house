use std::cell::RefCell;
use std::sync::Arc;
use std::thread;

fn main() {
    let shared = Arc::new(RefCell::new(0));
    let other = Arc::clone(&shared);
    let handle = thread::spawn(move || {
        *other.borrow_mut() += 1;
    });
    handle.join().unwrap();
}
//@ expect: E0277
