// 갈래를 여럿 둘 수 있다 — 위에서부터 처음 맞는 패턴으로 펼친다.
macro_rules! area {
    ($side:expr) => {
        $side * $side
    };
    ($w:expr, $h:expr) => {
        $w * $h
    };
}

fn main() {
    println!("{} {}", area!(3), area!(3, 4));
}
