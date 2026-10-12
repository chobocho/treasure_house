use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::thread;

fn main() {
    let input = AtomicU32::new(0);
    let go = AtomicBool::new(false);

    thread::scope(|s| {
        let worker = s.spawn(|| {
            // 깃발이 설 때까지 돌면서 묻는다.
            while !go.load(Ordering::SeqCst) {
                thread::yield_now(); // 차례를 양보하고 다시 묻는다
            }
            input.load(Ordering::SeqCst) * 2
        });

        input.store(21, Ordering::SeqCst); // 재료를 놓고
        go.store(true, Ordering::SeqCst); // 깃발을 세운다
        println!("일꾼의 답: {}", worker.join().unwrap());
    });
}
