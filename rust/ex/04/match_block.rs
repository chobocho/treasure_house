fn main() {
    let n = 7;
    let text = match n % 2 {
        0 => String::from("짝"),
        _ => {
            // 갈래가 길면 블록으로 — 마지막 식이 값이다.
            let half = n / 2;
            format!("홀 (반은 {half})")
        }
    };
    println!("{text}");
}
