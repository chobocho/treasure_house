use std::sync::mpsc;
use std::thread;

// 일감 — 한 번 불러 수 하나를 받는 클로저를 상자에 담은 것.
type Job = Box<dyn FnOnce() -> u32 + Send>;

fn main() {
    let (tx, rx) = mpsc::channel::<Job>();

    // 일꾼은 받은 차례대로 일하고, 답을 모아 돌려준다.
    let worker = thread::spawn(move || {
        let mut answers = Vec::new();
        for job in rx {
            answers.push(job());
        }
        answers
    });

    let base = 100;
    let words = vec!["가", "나", "다"];
    tx.send(Box::new(|| 6 * 7)).unwrap();
    tx.send(Box::new(move || base + 1)).unwrap();
    tx.send(Box::new(move || words.len() as u32)).unwrap();
    drop(tx); // 일감이 더 없다

    println!("{:?}", worker.join().unwrap());
}
