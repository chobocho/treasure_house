// 디버그 빌드는 정수 넘침에서 패닉, 릴리스 빌드는 조용히 감싼다.
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let score: u8 = 250 + args.len() as u8; // 상수 접기 피하기
    println!("score = {score}");
    let bonus = score + 10;
    println!("bonus = {bonus}");
    println!("wrapping  = {}", score.wrapping_add(10));
    println!("checked   = {:?}", score.checked_add(10));
    println!("saturating = {}", score.saturating_add(10));
}
