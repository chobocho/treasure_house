use std::sync::mpsc::{self, SendError};
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    drop(rx); // 받는 쪽이 사라졌다
    let letter = String::from("부치지 못한 편지");
    let err: SendError<String> = tx.send(letter).unwrap_err();
    println!("{err}");
    let back: String = err.0; // 보내려던 값이 그 안에 있다
    println!("돌려받았다: {back}");

    // 자리가 0 인 채널 — 받아 가야만 send 가 성공한다.
    let (tx, rx) = mpsc::sync_channel(0);
    let producer = thread::spawn(move || {
        let mut n = 1;
        // 받는 쪽이 사라지면 Err 가 못 보낸 값을 들고 돌아온다.
        loop {
            match tx.send(n) {
                Ok(()) => n += 1,
                Err(SendError(back)) => break back,
            }
        }
    });
    let first: Vec<u32> = rx.iter().take(3).collect();
    drop(rx);
    println!("받은 값: {first:?}");
    println!("못 보낸 값: {}", producer.join().unwrap());
}
