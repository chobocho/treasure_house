use std::thread;

fn main() {
    let names = vec!["kim", "lee"];
    // move — 클로저가 names 를 빌리지 않고 가져간다.
    let handle = thread::spawn(move || {
        println!("{names:?}");
    });
    handle.join().unwrap();
}
