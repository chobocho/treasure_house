use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        for n in 1..=3 {
            tx.send(n * 10).unwrap();
        }
    }); // 스레드가 끝나며 tx 가 사라진다

    // 보내는 쪽이 다 사라지면 반복이 끝난다.
    for value in rx {
        println!("{value}");
    }
    println!("채널이 닫혔다");
}
