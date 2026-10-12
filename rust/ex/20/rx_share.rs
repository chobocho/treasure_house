use std::sync::{Arc, mpsc};
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel::<u32>();
    let rx = Arc::new(rx);

    let mut workers = Vec::new();
    for _ in 0..2 {
        let rx = Arc::clone(&rx);
        workers.push(thread::spawn(move || {
            let mut sum = 0;
            loop {
                let got = rx.recv();
                let Ok(n) = got else { break };
                sum += n;
            }
            sum
        }));
    }

    for n in 1..=10 {
        tx.send(n).unwrap();
    }
    drop(tx); // 일이 더 없다
    let mut total = 0;
    for w in workers {
        total += w.join().unwrap();
    }
    println!("두 일꾼이 더한 합: {total}");
}
//@ expect: E0277
