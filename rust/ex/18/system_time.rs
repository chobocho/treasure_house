use std::time::{Duration, SystemTime, UNIX_EPOCH};

// from 에서 to 까지 — to 가 앞서면 duration_since 는 Err 다
fn gap(from: SystemTime, to: SystemTime) -> String {
    match to.duration_since(from) {
        Ok(d) => format!("{d:?} 뒤"),
        Err(e) => format!("{:?} 앞 ({e})", e.duration()),
    }
}

fn main() {
    // 지금 시각 — 기준 시각에서 얼마나 지났는지로 받는다
    let now = SystemTime::now();
    let since = now.duration_since(UNIX_EPOCH);
    println!("since.is_ok()        {}", since.is_ok());
    // 초 수는 실행마다 다르다. 2023년 11월 14일보다 뒤인지만 본다
    let secs = since.unwrap().as_secs();
    println!("secs > 1_700_000_000 {}", secs > 1_700_000_000);

    // 앞뒤를 바꾸면 Err 다
    let back = UNIX_EPOCH.duration_since(now);
    println!("back.is_err()        {}", back.is_err());

    // 기준에 길이를 더해 만든 시각은 수까지 정해진다
    let day = Duration::from_secs(86_400);
    let t: SystemTime = UNIX_EPOCH + day * 3;
    println!("{}", gap(UNIX_EPOCH, t));
    println!("{}", gap(t, UNIX_EPOCH));
    println!("t < now              {}", t < now);
}
