fn main() {
    // 본문이 여러 줄이면 중괄호로 묶는다 — 마지막 식이 값이다
    let describe = |n: i32| {
        let kind = if n % 2 == 0 { "짝수" } else { "홀수" };
        format!("{n} 은 {kind}")
    };
    println!("{}", describe(7));
    println!("{}", describe(10));

    let bad: Result<i32, String> = Err(String::from("abc"));
    // 받은 값을 쓰는 클로저
    let len = bad.clone().unwrap_or_else(|e| e.len() as i32);
    // 받기는 하지만 쓰지 않을 때는 이름 대신 _ 를 적는다
    let fallback = bad.unwrap_or_else(|_| -1);
    println!("{len} {fallback}");
}
