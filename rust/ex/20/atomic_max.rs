use std::sync::atomic::{AtomicU32, Ordering::SeqCst};
use std::thread;

// value 가 더 크면 올린다. 그새 값이 바뀌었으면 다시 견준다.
fn raise(max: &AtomicU32, value: u32) {
    let mut seen = max.load(SeqCst);
    while value > seen {
        match max.compare_exchange(seen, value, SeqCst, SeqCst) {
            Ok(_) => break,
            Err(now) => seen = now,
        }
    }
}

fn main() {
    let by_hand = AtomicU32::new(0);
    let by_method = AtomicU32::new(0);

    thread::scope(|s| {
        for scores in [[3, 41, 7], [29, 5, 38], [12, 40, 1]] {
            let (by_hand, by_method) = (&by_hand, &by_method);
            s.spawn(move || {
                for score in scores {
                    raise(by_hand, score);
                    by_method.fetch_max(score, SeqCst);
                }
            });
        }
    });

    println!("손으로 돈 반복문: {}", by_hand.load(SeqCst));
    println!("fetch_max: {}", by_method.load(SeqCst));
}
