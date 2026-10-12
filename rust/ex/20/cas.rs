use std::sync::atomic::{AtomicBool, AtomicU32, Ordering::SeqCst};
use std::thread;

fn main() {
    let n = AtomicU32::new(5);
    // "지금 5 라면 6 으로" — 견주기와 바꾸기가 한 번에 일어난다.
    println!("{:?}", n.compare_exchange(5, 6, SeqCst, SeqCst));
    // 이제 5 가 아니다. 바꾸지 않고 지금 값을 Err 로 알려 준다.
    println!("{:?}", n.compare_exchange(5, 7, SeqCst, SeqCst));
    println!("지금: {}", n.load(SeqCst));

    // 여덟 스레드가 깃발 하나를 서로 세우려 한다.
    let taken = AtomicBool::new(false);
    let winners = thread::scope(|s| {
        let handles: Vec<_> = (0..8)
            .map(|_| {
                s.spawn(|| {
                    taken
                        .compare_exchange(false, true, SeqCst, SeqCst)
                        .is_ok()
                })
            })
            .collect();
        handles
            .into_iter()
            .map(|h| h.join().unwrap())
            .filter(|won| *won)
            .count()
    });
    println!("깃발을 세운 스레드: {winners}");
}
