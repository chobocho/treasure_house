use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    let workers: Vec<_> = (1..=3)
        .map(|id| {
            let tx = tx.clone();
            thread::spawn(move || tx.send(id * 100).unwrap())
        })
        .collect();
    for w in workers {
        w.join().unwrap(); // 셋 다 보내고 끝났다
    }

    // 원본 tx 는 아직 살아 있다.
    let mut now: Vec<i32> = rx.try_iter().collect();
    now.sort();
    println!("지금 있는 것: {now:?}");
    println!("한 번 더: {:?}", rx.try_iter().collect::<Vec<_>>());

    tx.send(1).unwrap();
    tx.send(2).unwrap();
    drop(tx); // 이제 보낼 쪽이 없다
    println!("버린 뒤: {:?}", rx.try_iter().collect::<Vec<_>>());
}
