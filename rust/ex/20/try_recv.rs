use std::sync::mpsc::{self, Receiver, TryRecvError};
use std::thread;

fn look(rx: &Receiver<u32>) -> String {
    match rx.try_recv() {
        Ok(n) => format!("값 {n}"),
        Err(TryRecvError::Empty) => String::from("아직 없다"),
        Err(TryRecvError::Disconnected) => String::from("끝났다"),
    }
}

fn main() {
    let (tx, rx) = mpsc::channel();
    println!("{}", look(&rx)); // 보낸 적이 없다

    let worker = thread::spawn(move || {
        tx.send(7).unwrap();
        // 클로저가 끝나며 tx 가 사라진다
    });
    worker.join().unwrap(); // 보내고 끝나기를 기다렸다

    println!("{}", look(&rx)); // 들어 있던 값
    println!("{}", look(&rx)); // 비었고 보낼 쪽도 없다
}
