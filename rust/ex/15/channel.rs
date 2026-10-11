use std::sync::mpsc;
use std::thread;

fn main() {
    // tx 로 보내고 rx 로 받는다.
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        tx.send(String::from("안녕")).unwrap();
    });

    let msg = rx.recv().unwrap(); // 올 때까지 기다린다
    println!("받았다: {msg}");
}
