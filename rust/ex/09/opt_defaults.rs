// 기본값을 만드는 데 일이 드는 함수라고 하자.
fn compute(base: u32) -> u32 {
    println!("(기본값을 계산한다)");
    base * 2 + 1
}

fn main() {
    let some: Option<u32> = Some(8080);
    let none: Option<u32> = None;

    println!("{} {}", some.unwrap_or(80), none.unwrap_or(80));
    // 클로저는 None 일 때만 불린다 — 일을 그때까지 미룬다.
    println!("{}", some.unwrap_or_else(|| compute(40)));
    println!("{}", none.unwrap_or_else(|| compute(40)));
    // 타입의 기본값(u32 는 0).
    println!("{}", none.unwrap_or_default());
}
