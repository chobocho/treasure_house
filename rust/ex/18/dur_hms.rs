use std::time::Duration;

// 길이를 시:분:초로 적는다. 초 아래는 버린다
fn hms(d: Duration) -> String {
    let secs = d.as_secs();
    let (h, m, s) = (secs / 3600, secs / 60 % 60, secs % 60);
    format!("{h}:{m:02}:{s:02}")
}

fn main() {
    let movie = Duration::from_secs(2 * 3600 + 5 * 60 + 9);
    // {:?} 는 초로 적는다
    println!("{movie:?}");
    println!("{}", hms(movie));

    println!("{}", hms(Duration::from_secs(59)));
    println!("{}", hms(Duration::from_secs(3600)));
    println!("{}", hms(Duration::from_millis(61_900)));
    // 하루를 넘으면 시가 24 를 넘는다
    println!("{}", hms(Duration::from_secs(100_000)));

    // {:?} 에도 자릿수를 줄 수 있다
    let lap = Duration::from_nanos(1_234_567_890);
    println!("{lap:?} {lap:.2?} {lap:.0?}");
}
