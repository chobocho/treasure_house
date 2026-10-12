use std::cmp::Ordering as CmpOrdering;
use std::sync::atomic::{AtomicU32, Ordering};
use std::thread;

fn main() {
    // 원자 연산에 주는 Ordering — 변형이 다섯이다.
    let all = [
        Ordering::Relaxed,
        Ordering::Release,
        Ordering::Acquire,
        Ordering::AcqRel,
        Ordering::SeqCst,
    ];
    println!("{all:?}");

    let relaxed = AtomicU32::new(0);
    let seq_cst = AtomicU32::new(0);
    thread::scope(|s| {
        for _ in 0..4 {
            s.spawn(|| {
                for _ in 0..1000 {
                    relaxed.fetch_add(1, Ordering::Relaxed);
                    seq_cst.fetch_add(1, Ordering::SeqCst);
                }
            });
        }
    });
    let (a, b) = (relaxed.into_inner(), seq_cst.into_inner());
    println!("Relaxed 로 센 수 {a}, SeqCst 로 센 수 {b}");

    // 크기를 견준 답 Ordering 은 이름만 같은 다른 타입이다.
    let same: CmpOrdering = a.cmp(&b);
    println!("{same:?}");
}
