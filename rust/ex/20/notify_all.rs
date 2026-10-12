use std::sync::{Condvar, Mutex};
use std::thread;

struct Gate {
    waiting: u32,
    open: bool,
}

fn main() {
    let gate = Mutex::new(Gate {
        waiting: 0,
        open: false,
    });
    let arrived = Condvar::new(); // 기다리는 쪽이 하나 늘었다
    let opened = Condvar::new(); // 문이 열렸다

    let passed: u32 = thread::scope(|s| {
        let waiters: Vec<_> = (0..3)
            .map(|_| {
                s.spawn(|| {
                    let mut g = gate.lock().unwrap();
                    g.waiting += 1;
                    arrived.notify_one();
                    while !g.open {
                        g = opened.wait(g).unwrap();
                    }
                    1
                })
            })
            .collect();

        // 셋이 모두 잠든 것을 확인한 뒤에 문을 연다.
        let mut g = gate.lock().unwrap();
        while g.waiting < 3 {
            g = arrived.wait(g).unwrap();
        }
        g.open = true;
        drop(g);
        opened.notify_all();
        waiters.into_iter().map(|w| w.join().unwrap()).sum()
    });
    println!("문을 지난 스레드: {passed}");
}
