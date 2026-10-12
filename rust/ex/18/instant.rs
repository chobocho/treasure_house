use std::thread;
use std::time::{Duration, Instant};

fn main() {
    let nap = Duration::from_millis(20);

    // 지금 이 순간을 적어 두고, 잠깐 잔 뒤 다시 적는다
    let start = Instant::now();
    thread::sleep(nap);
    let end = Instant::now();

    // 두 순간은 견줄 수 있다
    println!("start < end        {}", start < end);
    // 두 순간의 차이는 Duration 이다
    let took: Duration = end.duration_since(start);
    println!("took >= nap        {}", took >= nap);
    println!("end - start        {}", end - start == took);

    // 순간에 길이를 더하면 다시 순간이다
    let wake: Instant = start + nap;
    println!("start + nap <= end {}", wake <= end);

    // elapsed — 그 순간부터 지금까지
    println!("elapsed >= took    {}", start.elapsed() >= took);

    // 앞뒤를 바꿔 빼면 0 이고, checked 는 None 이다
    println!("{:?}", start.duration_since(end));
    println!("{:?}", start.checked_duration_since(end));
}
