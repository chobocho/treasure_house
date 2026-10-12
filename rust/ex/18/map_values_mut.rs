use std::collections::HashMap;

fn main() {
    let mut price =
        HashMap::from([("사과", 1000), ("배", 2500), ("감", 800)]);
    // 값만 돌며 고친다 — 모두 10% 올린다
    for p in price.values_mut() {
        *p += *p / 10;
    }
    // 키를 보고 값을 고친다 — iter_mut 는 (&키, &mut 값) 을 낸다
    for (name, p) in price.iter_mut() {
        if *name == "배" {
            *p -= 500;
        }
    }
    // 하나만 고칠 때는 get_mut — 없는 키면 None
    if let Some(p) = price.get_mut("감") {
        *p = 900;
    }
    println!("{:?}", price.get_mut("잣"));

    let mut rows: Vec<_> = price.iter().collect();
    rows.sort();
    println!("{rows:?}");
    let total: u32 = price.values().sum();
    println!("{total}");
}
