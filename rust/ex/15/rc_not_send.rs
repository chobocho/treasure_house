use std::rc::Rc;
use std::thread;

fn main() {
    let shared = Rc::new(5);
    let other = Rc::clone(&shared);
    let handle = thread::spawn(move || {
        println!("{other}");
    });
    handle.join().unwrap();
}
//@ expect: E0277
