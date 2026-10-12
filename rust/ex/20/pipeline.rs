use std::sync::mpsc;
use std::thread;

fn main() {
    let (line_tx, line_rx) = mpsc::sync_channel::<&str>(1);
    let (count_tx, count_rx) = mpsc::sync_channel::<usize>(1);

    // 1단계 — 줄을 만들어 보낸다.
    let produce = thread::spawn(move || {
        for line in ["to be", "or not to be", "that is all"] {
            line_tx.send(line).unwrap();
        }
        // line_tx 가 사라지며 첫 채널이 닫힌다
    });

    // 2단계 — 줄을 받아 낱말 수로 바꿔 보낸다.
    let transform = thread::spawn(move || {
        for line in line_rx {
            count_tx.send(line.split_whitespace().count()).unwrap();
        }
        // 첫 채널이 닫히면 여기로 와서 둘째 채널도 닫힌다
    });

    // 3단계 — 모은다.
    let collect = thread::spawn(move || {
        let counts: Vec<usize> = count_rx.iter().collect();
        let total: usize = counts.iter().sum();
        (counts, total)
    });

    produce.join().unwrap();
    transform.join().unwrap();
    let (counts, total) = collect.join().unwrap();
    println!("줄마다 {counts:?}, 모두 {total} 낱말");
}
