fn classify(n: i32) -> &'static str {
    // 블록에도 이름표를 붙일 수 있다. break 로 값을 들고 빠져나온다.
    let kind = 'check: {
        if n < 0 {
            break 'check "음수";
        }
        if n == 0 {
            break 'check "영";
        }
        "양수"
    };
    kind
}

fn main() {
    println!("{} {} {}", classify(-3), classify(0), classify(8));
}
