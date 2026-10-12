use std::thread;
use std::time::{Duration, Instant};

// 될 때까지 다시 해 보되, 마감이 지나면 그만둔다.
// Ok(몇 번째에 됐나) 또는 Err(몇 번 해 봤나)
fn retry(
    limit: Duration,
    mut job: impl FnMut(u32) -> bool,
) -> Result<u32, u32> {
    let deadline = Instant::now() + limit;
    let mut tries = 0;
    loop {
        tries += 1;
        if job(tries) {
            return Ok(tries);
        }
        if Instant::now() >= deadline {
            return Err(tries);
        }
        thread::sleep(Duration::from_millis(2));
    }
}

fn main() {
    // 세 번째에 되는 일 — 마감은 넉넉히 1 분
    println!("{:?}", retry(Duration::from_secs(60), |n| n == 3));

    // 마감이 0 이어도 한 번은 해 본다
    println!("{:?}", retry(Duration::ZERO, |_| false));

    // 끝내 안 되는 일 — 마감 10 밀리초
    let limit = Duration::from_millis(10);
    let start = Instant::now();
    let r = retry(limit, |_| false);
    // 몇 번 해 봤는지는 실행마다 다를 수 있어 찍지 않는다
    println!("{} {}", r.is_err(), start.elapsed() >= limit);
}
