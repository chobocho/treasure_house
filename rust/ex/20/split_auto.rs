use std::io;
use std::num::NonZero;
use std::thread;

fn chunk_len(len: usize, threads: usize) -> usize {
    len.div_ceil(threads).max(1)
}

fn par_sum(xs: &[u64], threads: usize) -> u64 {
    let size = chunk_len(xs.len(), threads);
    thread::scope(|s| {
        let mut handles = Vec::new();
        for chunk in xs.chunks(size) {
            handles.push(s.spawn(move || chunk.iter().sum::<u64>()));
        }
        handles.into_iter().map(|h| h.join().unwrap()).sum()
    })
}

fn main() {
    // 이 기계에서 함께 돌릴 만한 스레드 수 — 값은 찍지 않는다.
    let avail: io::Result<NonZero<usize>> =
        thread::available_parallelism();
    let threads: usize = avail.map_or(1, |n| n.get());
    println!("1 이상인가: {}", threads >= 1);

    let xs: Vec<u64> = (1..=100).collect();
    let seq: u64 = xs.iter().sum();
    println!("차례로 더한 합: {seq}");
    println!("나눠 더한 합과 같은가: {}", par_sum(&xs, threads) == seq);

    // 스레드 수를 손으로 바꿔도 답은 같다.
    for n in [1, 2, 3, 7, 200] {
        println!("{n} 스레드: {}", par_sum(&xs, n) == seq);
    }
    println!("원소 셋: {}", par_sum(&xs[..3], threads));
    println!("빈 슬라이스: {}", par_sum(&[], threads));
}
