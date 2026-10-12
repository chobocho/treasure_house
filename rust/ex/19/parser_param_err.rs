// 같은 것을 타입 인자로 썼다.
trait Parser<T> {
    fn parse(&self, text: &str) -> Option<T>;
}

struct Number;

impl Parser<i64> for Number {
    fn parse(&self, text: &str) -> Option<i64> {
        text.trim().parse().ok()
    }
}

// 소수점이 있는 수도 읽게 구현을 하나 더 붙였다.
impl Parser<f64> for Number {
    fn parse(&self, text: &str) -> Option<f64> {
        text.trim().parse().ok()
    }
}

fn parse_all<T, P: Parser<T>>(p: &P, texts: &[&str]) -> Vec<Option<T>> {
    texts.iter().map(|t| p.parse(t)).collect()
}

fn main() {
    let nums = parse_all(&Number, &["42", " -7 ", "x"]);
    println!("{}", nums.len());
}
//@ expect: E0283
