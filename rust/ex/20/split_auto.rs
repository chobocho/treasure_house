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

// 기계가 답하지 못하면 스레드 하나로 한다.
fn thread_count(avail: io::Result<NonZero<usize>>) -> usize {
    avail.map_or(1, |n| n.get())
}

fn main() {
    // 답을 손으로 만들어 두 갈래를 다 지나 본다.
    let four = NonZero::new(4).unwrap();
    println!("Ok(4) 일 때: {}", thread_count(Ok(four)));
    let unknown = io::Error::other("알 수 없다");
    println!("Err 일 때: {}", thread_count(Err(unknown)));

    // 이 기계가 답한 수 — 값은 찍지 않는다.
    let threads = thread_count(thread::available_parallelism());
    println!("1 이상인가: {}", threads >= 1);
    let xs: Vec<u64> = (1..=100).collect();
    let seq: u64 = xs.iter().sum();
    println!("차례로 더한 합: {seq}");
    println!("나눠 더한 합과 같은가: {}", par_sum(&xs, threads) == seq);
    // 스레드 수를 손으로 바꿔도 답은 같다.
    for n in [1, 2, 3, 7] {
        println!("{n} 스레드: {}", par_sum(&xs, n) == seq);
    }
    println!("원소 셋을 200 스레드로: {}", par_sum(&xs[..3], 200));
    println!("빈 슬라이스: {}", par_sum(&[], threads));
}
