use std::thread;

fn main() {
    let names = vec!["kim", "lee"];
    let handle = thread::spawn(|| {
        println!("{names:?}");
    });
    handle.join().unwrap();
}
//@ expect: E0373
