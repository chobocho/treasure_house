fn describe(age: u32) -> String {
    match age {
        // 이름 @ 패턴 — 패턴에 맞는지 보면서, 맞은 값에 이름도 붙인다.
        n @ 0..=12 => format!("어린이({n})"),
        n @ 13..=19 => format!("청소년({n})"),
        n => format!("어른({n})"),
    }
}

fn main() {
    println!("{} {} {}", describe(7), describe(15), describe(40));
}
