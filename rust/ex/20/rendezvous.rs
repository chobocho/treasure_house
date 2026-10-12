use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc;
use std::thread;

fn main() {
    // 자리가 0 — 값이 채널 안에 머무를 곳이 없다.
    let (tx, rx) = mpsc::sync_channel::<&str>(0);

    // 받으러 온 스레드가 없으니 건넬 수 없다.
    println!("{:?}", tx.try_send("편지"));

    let arrived = Arc::new(AtomicUsize::new(0));
    let mark = Arc::clone(&arrived);
    let receiver = thread::spawn(move || {
        mark.fetch_add(1, Ordering::SeqCst); // 받으러 왔다
        rx.recv().unwrap()
    });

    tx.send("편지").unwrap();
    // send 가 돌아왔을 때 받는 쪽은 이미 와 있었다.
    println!("와 있던 쪽: {}", arrived.load(Ordering::SeqCst));
    println!("받은 것: {}", receiver.join().unwrap());
}
