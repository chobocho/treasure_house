use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::sync_channel(1);
    let passed = Arc::new(AtomicUsize::new(0));
    let mark = Arc::clone(&passed);

    let producer = thread::spawn(move || {
        tx.send(1).unwrap(); // 빈자리에 들어간다
        tx.send(2).unwrap(); // 자리가 없다
        mark.fetch_add(1, Ordering::SeqCst); // 둘째 send 를 지났다
        tx.send(3).unwrap();
    });

    // 아무것도 꺼내지 않은 채로 잠깐 둔다.
    thread::sleep(Duration::from_millis(20));
    let before = passed.load(Ordering::SeqCst);
    println!("둘째 send 를 지난 횟수: {before}");

    let got: Vec<i32> = rx.iter().collect();
    producer.join().unwrap();
    println!("받은 값: {got:?}");
    let after = passed.load(Ordering::SeqCst);
    println!("둘째 send 를 지난 횟수: {after}");
}
