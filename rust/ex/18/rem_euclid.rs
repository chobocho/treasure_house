const DAYS: [&str; 7] = ["월", "화", "수", "목", "금", "토", "일"];

fn main() {
    let today: i32 = 2; // 수요일
    // 10 일 뒤 — 양수에서는 % 와 rem_euclid 가 같다
    let after = today + 10;
    println!("{} {}", after % 7, after.rem_euclid(7));
    // 5 일 전 — 왼쪽이 음수면 % 의 결과도 음수다
    let before = today - 5;
    println!("{} {}", before % 7, before.rem_euclid(7));
    let i = before.rem_euclid(7) as usize;
    println!("5 일 전은 {}요일", DAYS[i]);

    // 몫 × 7 + 나머지 = 원래 값 — 두 짝 모두 성립한다
    let (q, r) = (before / 7, before % 7);
    println!("/ 와 %    {q} × 7 + {r} = {}", q * 7 + r);
    let (q, r) = (before.div_euclid(7), before.rem_euclid(7));
    println!("euclid    {q} × 7 + {r} = {}", q * 7 + r);
}
