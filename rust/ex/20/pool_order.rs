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
    tx: Option<Sender<Job>>,
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
        Pool {
            tx: Some(tx),
            workers,
        }
    }

    fn execute(&self, job: impl FnOnce() + Send + 'static) {
        let Some(tx) = &self.tx else { return };
        tx.send(Box::new(job)).unwrap();
    }
}

impl Drop for Pool {
    fn drop(&mut self) {
        // 보내는 쪽을 버린다 — 일꾼의 recv 가 Err 로 돌아온다.
        drop(self.tx.take());
        for w in std::mem::take(&mut self.workers) {
            w.join().unwrap();
        }
    }
}

fn main() {
    let words = ["사과", "배", "복숭아", "감", "산딸기"];
    let pool = Pool::new(3);
    let (out_tx, out_rx) = mpsc::channel();
    for (i, word) in words.iter().enumerate() {
        let word = word.to_string();
        let out = out_tx.clone();
        // 일은 자기 번호 i 를 결과와 함께 보낸다.
        pool.execute(move || {
            let n = word.chars().count();
            out.send((i, n)).unwrap();
        });
    }
    drop(out_tx);

    // 도착한 순서가 아니라 번호가 가리키는 칸에 넣는다.
    let mut lens = vec![0; words.len()];
    for (i, n) in out_rx {
        lens[i] = n;
    }
    println!("{words:?}");
    println!("{lens:?}");
}
