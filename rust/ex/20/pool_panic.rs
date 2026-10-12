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
        let mut dead = 0;
        for w in std::mem::take(&mut self.workers) {
            if w.join().is_err() {
                dead += 1;
            }
        }
        println!("패닉으로 끝난 일꾼: {dead}");
    }
}

fn main() {
    let (out_tx, out_rx) = mpsc::channel();
    {
        let pool = Pool::new(3);
        for i in 0..6usize {
            let out = out_tx.clone();
            pool.execute(move || {
                if i == 2 {
                    panic!("2번 일이 쓰러졌다");
                }
                out.send((i, i * 10)).unwrap();
            });
        }
    }
    let mut slots = vec![None; 6];
    for (i, value) in out_rx.try_iter() {
        slots[i] = Some(value);
    }
    println!("{slots:?}");
}
