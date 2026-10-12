// 점수 한 칸을 읽는다. 못 읽은 것은 알리고 0 으로 친다
fn score(text: &str) -> u32 {
    text.trim()
        .parse::<u32>()
        .inspect_err(|e| println!("  {text:?}: {e}"))
        .unwrap_or_default()
}

fn main() {
    let inputs = ["72", " 91 ", "결석", "-5"];
    let scores: Vec<u32> = inputs.iter().map(|s| score(s)).collect();
    println!("{scores:?}");

    // inspect_err 는 받은 Result 를 그대로 돌려준다
    let seen = "x".parse::<u32>().inspect_err(|_| println!("  (봤다)"));
    println!("{}", seen.is_err());
    // Ok 일 때는 클로저를 부르지 않는다
    let seen = "7".parse::<u32>().inspect_err(|_| println!("  (봤다)"));
    println!("{seen:?}");

    // ok 는 값 쪽만, err 는 오류 쪽만 Option 으로 꺼낸다
    let good: Result<u32, &str> = Ok(3);
    let bad: Result<u32, &str> = Err("고장");
    println!("{:?} {:?}", good.ok(), good.err());
    println!("{:?} {:?}", bad.ok(), bad.err());

    // 실패한 칸의 까닭만 모은다
    let why: Vec<String> = inputs
        .iter()
        .filter_map(|s| s.trim().parse::<u32>().err())
        .map(|e| e.to_string())
        .collect();
    println!("{why:?}");
}
