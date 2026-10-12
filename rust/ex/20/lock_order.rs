use std::sync::Mutex;
use std::thread;

// 어느 쪽으로 보내든 번호가 작은 계좌부터 잠근다.
fn transfer(bank: &[Mutex<i64>], from: usize, to: usize, amount: i64) {
    if from == to {
        return; // 같은 잠금을 두 번 잡지 않는다
    }
    let mut src;
    let mut dst;
    if from < to {
        src = bank[from].lock().unwrap();
        dst = bank[to].lock().unwrap();
    } else {
        dst = bank[to].lock().unwrap();
        src = bank[from].lock().unwrap();
    }
    *src -= amount;
    *dst += amount;
}

fn main() {
    let bank = [Mutex::new(1000), Mutex::new(1000)];

    thread::scope(|s| {
        s.spawn(|| {
            for _ in 0..1000 {
                transfer(&bank, 0, 1, 3);
            }
        });
        s.spawn(|| {
            for _ in 0..1000 {
                transfer(&bank, 1, 0, 1);
            }
        });
    });
    transfer(&bank, 0, 0, 500); // 자기에게 보내기

    let total: i64 = bank.iter().map(|m| *m.lock().unwrap()).sum();
    println!("두 계좌의 합: {total}");
}
