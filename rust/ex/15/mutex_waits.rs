use std::sync::mpsc;
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let log = Arc::new(Mutex::new(Vec::new()));
    let (tx, rx) = mpsc::channel();

    // main 이 먼저 잠근다 — 열쇠는 guard 가 쥔다
    let mut guard = log.lock().unwrap();

    let log2 = Arc::clone(&log);
    let handle = thread::spawn(move || {
        tx.send("worker 출발").unwrap();
        // 열쇠가 돌아올 때까지 lock 에서 기다린다
        log2.lock().unwrap().push("worker");
    });

    // worker 가 돌기 시작한 것을 확인한 뒤에 넣는다
    println!("{}", rx.recv().unwrap());
    guard.push("main");
    drop(guard); // 열쇠를 놓는다
    handle.join().unwrap();
    println!("{:?}", log.lock().unwrap());
}
