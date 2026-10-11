// 시그니처는 "결과는 a 에 매인다" 고 하는데, 본문은 b 를 돌려준다.
fn pick<'a>(a: &'a str, b: &str) -> &'a str {
    if a.is_empty() { b } else { a }
}

fn main() {
    println!("{}", pick("", "fallback"));
}
//@ expect: E0621
