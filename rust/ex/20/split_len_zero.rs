// 원소 len 개를 스레드 threads 개가 나눌 때 한 조각의 길이
fn chunk_len(len: usize, threads: usize) -> usize {
    // 올림 나눗셈. 빈 입력이면 0 이 나오므로 1 로 올린다.
    len.div_ceil(threads)
}

// 그 길이로 끊으면 조각이 몇 개인가 — 곧 만들 스레드의 수
fn pieces(len: usize, threads: usize) -> usize {
    vec![0u8; len].chunks(chunk_len(len, threads)).count()
}

fn main() {
    println!("10 / 4 = {}, 올림은 {}", 10 / 4, 10usize.div_ceil(4));

    for (len, threads) in [(10, 4), (3, 8), (0, 4)] {
        let size = chunk_len(len, threads);
        let count = pieces(len, threads);
        println!(
            "{len} 개를 {threads} 스레드로: 길이 {size}, 조각 {count}"
        );
    }
}
//@ exit: 101
