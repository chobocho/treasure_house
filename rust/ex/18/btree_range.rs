use std::collections::BTreeMap;

fn main() {
    // 시각(시 × 100 + 분) → 일정
    let mut plan = BTreeMap::from([
        (1300, "점심"),
        (900, "회의"),
        (1730, "회고"),
        (1030, "리뷰"),
        (1500, "배포"),
    ]);
    // 10 시부터 15 시 전까지
    for (time, what) in plan.range(1000..1500) {
        println!("{time} {what}");
    }
    // 15 시 정각까지 넣으려면 ..=
    println!("{}", plan.range(1000..=1500).count());
    // 14 시에 하고 있는 일 — 14 시까지의 항목 가운데 마지막
    println!("{:?}", plan.range(..=1400).next_back());
    // 14 시 뒤에 처음 오는 일정
    println!("{:?}", plan.range(1400..).next());
    // 8 시 전에는 아무것도 없다
    println!("{:?}", plan.range(..800).next_back());

    // 처음과 마지막, 그리고 처음 것을 꺼내기
    println!(
        "{:?} {:?}",
        plan.first_key_value(),
        plan.last_key_value()
    );
    println!("{:?} {}", plan.pop_first(), plan.len());
}
