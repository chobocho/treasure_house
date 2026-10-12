use std::thread;

// 일 하나 — 1 부터 n 까지 더한다
fn work(n: u64) -> u64 {
    (1..=n).sum()
}

fn main() {
    // 일이 하나 올 때마다 스레드를 하나 만든다.
    let mut handles = Vec::new();
    for n in 1..=20 {
        handles.push(thread::spawn(move || work(n)));
    }
    println!("일 20 개에 만든 스레드: {}", handles.len());

    let total: u64 =
        handles.into_iter().map(|h| h.join().unwrap()).sum();
    println!("결과의 합: {total}");
}
