use std::sync::mpsc;
use std::thread;

// 일 하나 — 한 번 부를 클로저를 상자에 담은 것
type Job = Box<dyn FnOnce() + Send>;

fn main() {
    let (job_tx, job_rx) = mpsc::channel::<Job>();
    let (done_tx, done_rx) = mpsc::channel::<String>();

    let worker = thread::spawn(move || {
        for job in job_rx {
            job(); // 받은 일을 한다
        }
    });

    let report = done_tx.clone();
    job_tx
        .send(Box::new(move || {
            let sum: u32 = (1..=10).sum();
            report.send(format!("합 {sum}")).unwrap();
        }))
        .unwrap();

    let word = String::from("채널");
    job_tx
        .send(Box::new(move || {
            let n = word.chars().count();
            done_tx.send(format!("{word}: {n} 글자")).unwrap();
        }))
        .unwrap();

    drop(job_tx); // 일이 더 없다
    worker.join().unwrap();
    for line in done_rx {
        println!("{line}");
    }
}
