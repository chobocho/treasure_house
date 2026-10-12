use std::collections::VecDeque;
use std::sync::{Condvar, Mutex};
use std::thread;

struct Queue<T> {
    items: Mutex<VecDeque<T>>,
    added: Condvar,
}

impl<T> Queue<T> {
    fn new() -> Self {
        Queue {
            items: Mutex::new(VecDeque::new()),
            added: Condvar::new(),
        }
    }

    fn push(&self, item: T) {
        self.items.lock().unwrap().push_back(item);
        self.added.notify_one();
    }

    // 비어 있으면 들어올 때까지 기다린다.
    fn pop(&self) -> T {
        let mut items = self.items.lock().unwrap();
        while items.is_empty() {
            items = self.added.wait(items).unwrap();
        }
        items.pop_front().unwrap()
    }
}

fn main() {
    let queue = Queue::new();
    thread::scope(|s| {
        s.spawn(|| {
            for n in 1..=5 {
                queue.push(n * 10);
            }
        });
        let got: Vec<u32> = (0..5).map(|_| queue.pop()).collect();
        println!("꺼낸 순서: {got:?}");
        println!("합: {}", got.iter().sum::<u32>());
    });
}
