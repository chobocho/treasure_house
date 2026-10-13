use std::collections::BTreeMap;

fn main() {
    let name = String::from("kim");
    let scores = vec![90, 85];
    let mut ages = BTreeMap::new();
    ages.insert("kim", 31);
    ages.insert("lee", 27);

    // {} 는 글자만, {:?} 는 따옴표까지 찍는다
    println!("{name} {name:?}");
    // 벡터와 맵은 {:?} 로 통째로 찍는다
    println!("{scores:?} {ages:?}");
    // {:#?} 는 한 줄에 하나씩 펼친다
    println!("{scores:#?}");
    // 폭과 정렬은 String 에도 그대로 쓴다
    println!("[{name:>6}] [{name:<6}] [{name:^7}]");
    // format! 은 찍지 않고 String 으로 돌려준다
    let line = format!("{name}: {scores:?}");
    println!("{line}");
}
