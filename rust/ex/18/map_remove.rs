use std::collections::HashMap;

type Stock = HashMap<&'static str, u32>;

// 키 순서로 늘어놓아 찍는다
fn show(stock: &Stock) {
    let mut rows: Vec<_> = stock.iter().collect();
    rows.sort();
    println!("{rows:?}");
}

fn main() {
    let mut stock: Stock = HashMap::from([
        ("사과", 3),
        ("배", 0),
        ("감", 5),
        ("귤", 0),
        ("밤", 2),
    ]);
    // 값은 필요 없고 있는지만 물을 때
    println!(
        "{} {}",
        stock.contains_key("배"),
        stock.contains_key("잣")
    );
    // remove 는 지운 값을 돌려준다 — 없는 키면 None
    println!("{:?} {:?}", stock.remove("감"), stock.remove("감"));
    // remove_entry 는 키와 값을 함께 돌려준다
    println!("{:?}", stock.remove_entry("귤"));
    show(&stock);
    // retain — 클로저가 true 를 낸 항목만 남긴다
    stock.retain(|_, count| *count > 0);
    show(&stock);
}
