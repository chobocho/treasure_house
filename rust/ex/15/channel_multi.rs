use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    for id in 1..=3 {
        let tx = tx.clone(); // 보내는 쪽은 여럿일 수 있다
        thread::spawn(move || {
            tx.send(id * 100).unwrap();
        });
    }
    drop(tx); // 원본도 버려야 채널이 닫힌다

    // 도착하는 순서는 실행마다 다를 수 있다 — 모은 뒤 정렬한다.
    let mut all: Vec<i32> = rx.iter().collect();
    all.sort();
    println!("{all:?}");
}
