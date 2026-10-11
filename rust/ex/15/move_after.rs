use std::thread;

fn main() {
    let names = vec!["kim", "lee"];
    let handle = thread::spawn(move || {
        println!("{names:?}");
    });
    println!("{names:?}");
    handle.join().unwrap();
}
//@ expect: E0382
