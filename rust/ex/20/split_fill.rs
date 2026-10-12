use std::thread;

// buf[i] 에 i 의 제곱을 채운다 — 조각마다 스레드 하나.
fn fill_squares(buf: &mut [u64], size: usize) {
    thread::scope(|s| {
        for (k, chunk) in buf.chunks_mut(size).enumerate() {
            s.spawn(move || {
                let start = k * size; // 이 조각의 첫 인덱스
                for (j, slot) in chunk.iter_mut().enumerate() {
                    let i = (start + j) as u64;
                    *slot = i * i;
                }
            });
        }
    });
}

fn main() {
    let mut buf = vec![0u64; 10];
    fill_squares(&mut buf, 4);
    println!("{buf:?}");

    let seq: Vec<u64> = (0..10).map(|i| i * i).collect();
    println!("차례로 채운 것과 같은가: {}", buf == seq);
}
