use std::sync::mpsc::{self, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

// 일 하나 — 한 번 부를 클로저를 상자에 담은 것
type Job = Box<dyn FnOnce() + Send + 'static>;

// 일꾼 하나가 도는 반복문
fn work(rx: &Mutex<Receiver<Job>>) {
    loop {
        // 열쇠는 이 let 문이 끝나며 사라진다.
        let job = rx.lock().unwrap().recv();
        let Ok(job) = job else { break };
        job();
    }
}

struct Pool {
    tx: Sender<Job>,
    workers: Vec<JoinHandle<()>>,
}

impl Pool {
    fn new(size: usize) -> Pool {
        let (tx, rx) = mpsc::channel::<Job>();
        let rx = Arc::new(Mutex::new(rx));
        let mut workers = Vec::new();
        for _ in 0..size {
            let rx = Arc::clone(&rx);
            workers.push(thread::spawn(move || work(&rx)));
        }
        Pool { tx, workers }
    }

    fn execute(&self, job: impl FnOnce() + Send + 'static) {
        self.tx.send(Box::new(job)).unwrap();
    }
}

fn main() {
    let pool = Pool::new(3);
    let (out_tx, out_rx) = mpsc::channel();
    for n in 1..=6u32 {
        let out = out_tx.clone();
        pool.execute(move || out.send(n * n).unwrap());
    }
    drop(out_tx);
    let mut squares: Vec<u32> = out_rx.iter().collect();
    squares.sort();
    println!("{squares:?}");

    // 끝내기 — 보내는 쪽을 버리고 일꾼을 하나씩 기다린다.
    drop(pool.tx);
    let mut ended = 0;
    for w in pool.workers {
        w.join().unwrap();
        ended += 1;
    }
    println!("끝난 일꾼: {ended}");
}
