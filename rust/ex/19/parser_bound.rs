use std::fmt::Debug;

trait Parser {
    // 조건을 트레이트에 한 번만 적는다.
    type Output: Debug;

    fn parse(&self, text: &str) -> Option<Self::Output>;
}

struct Int;

impl Parser for Int {
    type Output = i64;

    fn parse(&self, text: &str) -> Option<i64> {
        text.trim().parse().ok()
    }
}

// where 절이 없어도 Output 을 {:?} 로 찍는다.
fn show<P: Parser>(p: &P, text: &str) {
    println!("{text:?} -> {:?}", p.parse(text));
}

fn main() {
    show(&Int, "42");
    show(&Int, "x");
}
