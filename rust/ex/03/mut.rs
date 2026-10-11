fn main() {
    let mut score = 80;
    println!("처음: {score}");
    score = 95;
    println!("나중: {score}");
    // += 도 대입이다 — mut 가 있어야 한다
    score += 5;
    println!("가산: {score}");
}
