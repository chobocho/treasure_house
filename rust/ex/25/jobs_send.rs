use std::sync::Arc;
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

    // 값 목록 하나를 main 과 둘째 일감이 함께 갖는다.
    let prices = Arc::new(vec![30, 60, 11]);
    let shared = Arc::clone(&prices);
    tx.send(Box::new(|| 6 * 7)).unwrap();
    tx.send(Box::new(move || shared.iter().sum())).unwrap();
    let count = prices.len() as u32;
    tx.send(Box::new(move || count)).unwrap();
    drop(tx); // 일감이 더 없다

    println!("{:?}", worker.join().unwrap());
}
