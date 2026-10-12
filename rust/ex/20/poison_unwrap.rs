use std::sync::Mutex;
use std::thread;

fn report(scores: &Mutex<Vec<u32>>) {
    match scores.lock() {
        Ok(guard) => println!("잠갔다: {guard:?}"),
        Err(e) => println!("lock 이 Err 다: {e}"),
    }
}

fn main() {
    let scores = Mutex::new(vec![10, 20]);
    report(&scores);

    thread::scope(|s| {
        let worker = s.spawn(|| {
            let mut guard = scores.lock().unwrap();
            guard.push(30);
            panic!("열쇠를 쥔 채 쓰러졌다");
        });
        println!("일꾼이 패닉했나: {}", worker.join().is_err());
    });

    println!("독이 들었나: {}", scores.is_poisoned());
    println!("{:?}", scores.lock().unwrap());
}
//@ exit: 101
