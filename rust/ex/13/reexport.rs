mod engine {
    mod parser {
        pub fn parse(s: &str) -> usize {
            s.split(' ').count()
        }
    }

    // 안쪽 구조를 숨기고, 쓸 이름만 이 층에 다시 내놓는다.
    pub use parser::parse;
}

fn main() {
    // engine::parser::parse 가 아니라 engine::parse 로 쓴다.
    println!("{}", engine::parse("a b c"));
}
