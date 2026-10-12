use std::thread;

fn main() {
    let xs: Vec<u64> = (1..=10).collect();

    // 셋씩 끊은 조각마다 스레드 하나가 더한다.
    let sums: Vec<u64> = thread::scope(|s| {
        let mut handles = Vec::new();
        for chunk in xs.chunks(3) {
            handles.push(s.spawn(move || chunk.iter().sum::<u64>()));
        }
        // 만든 순서대로 기다려 조각의 순서대로 모은다.
        handles.into_iter().map(|h| h.join().unwrap()).collect()
    });
    println!("조각의 합: {sums:?}");

    let total: u64 = sums.iter().sum();
    let seq: u64 = xs.iter().sum();
    println!("나눠 더한 합 {total}, 차례로 더한 합 {seq}");
    println!("같은가: {}", total == seq);
}
