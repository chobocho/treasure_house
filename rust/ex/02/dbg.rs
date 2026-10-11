fn main() {
    let a = 5;
    // dbg! 는 식과 그 값을 찍고, 값을 그대로 돌려준다
    let b = dbg!(a * 2) + 1;
    println!("b = {b}");
    // 여러 개를 한꺼번에 줄 수도 있다
    dbg!(a, b);
}
