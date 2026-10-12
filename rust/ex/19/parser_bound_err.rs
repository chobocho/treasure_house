use std::fmt::Debug;

trait Parser {
    type Output: Debug;

    fn parse(&self, text: &str) -> Option<Self::Output>;
}

// Debug 를 붙이지 않은 타입
struct Token(String);

struct Lexer;

impl Parser for Lexer {
    type Output = Token;

    fn parse(&self, text: &str) -> Option<Token> {
        Some(Token(text.to_string()))
    }
}

fn main() {
    let token = Lexer.parse("let");
    println!("{}", token.is_some_and(|t| t.0 == "let"));
}
//@ expect: E0277
