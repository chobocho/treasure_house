use std::collections::HashMap;

fn main() {
    let records = [
        "pen in 30",
        "cup in 12",
        "pen out 8",
        "ink out 5",
        "cup out 12",
        "pen 4",
        "bag in 3",
        "cup lost 1",
        "pen in 4",
        "pen out 30",
    ];
    let mut stock: HashMap<&str, u32> = HashMap::new();
    for record in records {
        let words: Vec<&str> = record.split_whitespace().collect();
        let [name, kind, qty] = &words[..] else {
            println!("{record}: 낱말이 셋이 아니다");
            continue;
        };
        let qty: u32 = qty.parse().unwrap();
        let have = stock.get(*name).copied().unwrap_or(0);
        if *kind == "in" {
            *stock.entry(*name).or_insert(0) += qty;
        } else if *kind != "out" {
            println!("{record}: in 도 out 도 아니다");
        } else if have < qty {
            println!("{record}: 모자란다 (지금 {have}개)");
        } else if have == qty {
            stock.remove(*name);
        } else {
            stock.insert(*name, have - qty);
        }
    }
    let mut left: Vec<(&str, u32)> = stock.into_iter().collect();
    left.sort();
    for (name, n) in left {
        println!("{name:<4}{n:>3}");
    }
}
