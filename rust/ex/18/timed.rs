use std::thread;
use std::time::{Duration, Instant};

// 일을 시키고, 결과와 걸린 시간을 함께 돌려준다
fn timed<T>(job: impl FnOnce() -> T) -> (T, Duration) {
    let start = Instant::now();
    let value = job();
    (value, start.elapsed())
}

fn main() {
    // 걸린 시간은 실행마다 다르다 — 결과만 찍는다
    let (sum, _took) = timed(|| (1..=1000_u64).sum::<u64>());
    println!("{sum}");

    let (words, _took) = timed(|| "가 나 다".split(' ').count());
    println!("{words}");

    // 20 밀리초를 자는 일은 적어도 그만큼 걸린다
    let nap = Duration::from_millis(20);
    let (word, took) = timed(|| {
        thread::sleep(nap);
        "깼다"
    });
    println!("{word} {}", took >= nap);
}
