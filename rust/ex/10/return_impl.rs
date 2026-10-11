// 돌려주는 타입을 숨긴다 — "무언가 Iterator 인 것".
fn evens(limit: u32) -> impl Iterator<Item = u32> {
    (0..limit).filter(|n| n % 2 == 0)
}

fn main() {
    let v: Vec<u32> = evens(10).collect();
    println!("{v:?}");
}
