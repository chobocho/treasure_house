// 값을 둘 돌려주려면 튜플로 묶는다.
fn div_rem(a: i32, b: i32) -> (i32, i32) {
    (a / b, a % b)
}

fn main() {
    let (q, r) = div_rem(17, 5);
    println!("몫 {q}, 나머지 {r}");
    let both = div_rem(9, 4);
    println!("{} {}", both.0, both.1);
}
