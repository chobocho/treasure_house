trait Parser {
    type Output;
    fn parse(&self, text: &str) -> Option<Self::Output>;
}

struct Int;
struct Word;

impl Parser for Int {
    type Output = i64;
    fn parse(&self, text: &str) -> Option<i64> {
        text.trim().parse().ok()
    }
}

impl Parser for Word {
    type Output = String;
    fn parse(&self, text: &str) -> Option<String> {
        Some(text.trim().to_string())
    }
}

// "왼쪽=오른쪽" 을 읽는다. 두 파서를 이어 붙인 파서.
struct Pair<A, B>(A, B);

impl<A: Parser, B: Parser> Parser for Pair<A, B> {
    // 두 파서의 Output 으로 내 Output 을 짓는다.
    type Output = (A::Output, B::Output);
    fn parse(&self, text: &str) -> Option<Self::Output> {
        let (left, right) = text.split_once('=')?;
        Some((self.0.parse(left)?, self.1.parse(right)?))
    }
}

fn main() {
    let entry = Pair(Word, Int);
    println!("{:?}", entry.parse("port = 8080"));
    println!("{:?}", entry.parse("port = many"));
    println!("{:?}", entry.parse("no equals"));
    // 두 None 이 갈린 곳 — split_once 만 따로 불러 본다.
    println!("{:?}", "port = many".split_once('='));
    println!("{:?}", "no equals".split_once('='));
    let range = Pair(Int, Int);
    println!("{:?}", range.parse("3=9"));
}
