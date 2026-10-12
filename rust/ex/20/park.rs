use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;

fn main() {
    // 표를 먼저 받아 두면 park 는 바로 돌아온다.
    thread::current().unpark();
    thread::park();
    println!("표가 있어서 park 에서 바로 돌아왔다");

    let go = AtomicBool::new(false);
    thread::scope(|s| {
        let sleeper = s.spawn(|| {
            while !go.load(Ordering::SeqCst) {
                thread::park(); // 표가 올 때까지 잔다
            }
            "깨어났다"
        });

        go.store(true, Ordering::SeqCst);
        sleeper.thread().unpark(); // 손잡이로 그 스레드에 표를 준다
        println!("{}", sleeper.join().unwrap());
    });
}
