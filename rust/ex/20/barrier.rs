use std::sync::Barrier;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::thread;

fn main() {
    let barrier = Barrier::new(4); // 넷이 모여야 열린다
    let arrived = AtomicUsize::new(0);

    let results: Vec<(usize, bool)> = thread::scope(|s| {
        let handles: Vec<_> = (0..4)
            .map(|_| {
                s.spawn(|| {
                    arrived.fetch_add(1, Ordering::SeqCst); // 왔다
                    let leader = barrier.wait().is_leader();
                    // 지난 뒤에 세어 본다.
                    (arrived.load(Ordering::SeqCst), leader)
                })
            })
            .collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect()
    });

    let seen: Vec<usize> = results.iter().map(|r| r.0).collect();
    let leaders = results.iter().filter(|r| r.1).count();
    println!("지난 뒤에 본 도착 수: {seen:?}");
    println!("대표가 된 스레드: {leaders}");
}
