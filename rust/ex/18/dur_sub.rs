use std::time::Duration;

fn main() {
    let limit = Duration::from_secs(60);
    let short = Duration::from_secs(45);
    let long = Duration::from_secs(75);

    // 남은 시간 — 쓴 시간이 한도보다 짧으면 뺄 수 있다
    println!("{:?}", limit - short);

    // 한도를 넘겼을 때 — 음수인 길이는 없다
    println!("{:?}", limit.checked_sub(long));
    println!("{:?}", limit.checked_sub(short));
    println!("{:?}", limit.saturating_sub(long));
    println!("{}", limit.saturating_sub(long).is_zero());

    // 어느 쪽이 길든 차이만 — abs_diff
    println!("{:?} {:?}", limit.abs_diff(long), long.abs_diff(limit));

    // - 는 같은 경우에 패닉한다
    println!("{:?}", limit - long);
}
//@ exit: 101
