fn main() {
    let mut n = 27;
    let mut steps = 0;
    // 조건이 참인 동안 돈다 — 콜라츠 수열.
    while n != 1 {
        n = if n % 2 == 0 { n / 2 } else { 3 * n + 1 };
        steps += 1;
    }
    println!("{steps}번 만에 1");
}
