use std::collections::BTreeMap;

fn main() {
    let rolls = [3, 6, 1, 3, 5, 3, 6, 2, 6, 3, 1, 6];
    let mut counts = BTreeMap::new();
    for r in rolls {
        *counts.entry(r).or_insert(0) += 1;
    }
    let mut best = 0;
    let mut most = 0;
    for (face, n) in &counts {
        print!("{face}: ");
        for _ in 0..*n {
            print!("#");
        }
        println!(" {n}");
        // 같으면 바꾸지 않으므로 작은 눈이 남는다
        if *n > most {
            best = *face;
            most = *n;
        }
    }
    println!("가장 많이 나온 눈 {best}");
}
