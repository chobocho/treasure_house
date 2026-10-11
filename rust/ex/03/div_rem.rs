fn main() {
    // 정수끼리 나누면 몫만 남는다 — 소수점 아래는 0 쪽으로 버린다
    println!(" 7 / 2 = {}", 7 / 2);
    println!("-7 / 2 = {}", -7 / 2);
    // % 는 나머지 — 부호는 나뉘는 수(왼쪽)를 따른다
    println!(" 7 %  3 = {}", 7 % 3);
    println!("-7 %  3 = {}", -7 % 3);
    println!(" 7 % -3 = {}", 7 % -3);
    // rem_euclid 는 음수가 되지 않는 나머지를 준다
    let n: i32 = -7;
    println!("n.rem_euclid(3) = {}", n.rem_euclid(3));
    println!("n.div_euclid(3) = {}", n.div_euclid(3));
}
