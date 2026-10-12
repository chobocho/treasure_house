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

// Debug 를 붙이지 않은 타입을 Output 으로 정한다.
struct Token(String);
struct Lexer;

impl Parser for Lexer {
    type Output = Token;

    fn parse(&self, text: &str) -> Option<Token> {
        Some(Token(text.to_string()))
    }
}

fn main() {
    // Lexer 는 어디에도 넘기지 않는다.
    show(&Int, "42");
    show(&Int, "x");
}
//@ expect: E0277
