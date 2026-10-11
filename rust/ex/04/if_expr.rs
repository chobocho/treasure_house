fn main() {
    let score = 72;
    // if 는 값을 낸다 — 삼항 연산자(?:)가 따로 없다.
    let result = if score >= 60 { "합격" } else { "불합격" };
    println!("{result}");

    let abs = if score < 0 { -score } else { score };
    println!("{abs}");
}
