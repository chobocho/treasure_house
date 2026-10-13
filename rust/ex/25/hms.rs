const MINUTE: u32 = 60;
const HOUR: u32 = 60 * MINUTE;

fn main() {
    let total: u32 = 98_795;
    let h = total / HOUR;
    let m = total % HOUR / MINUTE;
    let s = total % MINUTE;
    println!("{total}초 = {h}:{m:02}:{s:02}");
    // 정수끼리 나누면 소수점 아래가 버려지므로 실수로 바꿔서 나눈다
    let hours = total as f64 / HOUR as f64;
    println!("{hours:.2}시간");
    let minutes = (total as f64 / MINUTE as f64).round() as u32;
    println!("반올림하면 {minutes}분, 버리면 {}분", total / MINUTE);
}
