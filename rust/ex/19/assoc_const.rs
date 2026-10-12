trait Parser {
    type Output;
    const NAME: &'static str;
    const MAX_LEN: usize;
    fn parse(&self, text: &str) -> Option<Self::Output>;
}

struct Int;
struct Flag;

impl Parser for Int {
    type Output = i64;
    const NAME: &'static str = "정수";
    const MAX_LEN: usize = 20;
    fn parse(&self, text: &str) -> Option<i64> {
        text.parse().ok()
    }
}

impl Parser for Flag {
    type Output = bool;
    const NAME: &'static str = "참거짓";
    const MAX_LEN: usize = 5;
    fn parse(&self, text: &str) -> Option<bool> {
        text.parse().ok()
    }
}

// 값이 아니라 타입 P 에 상수를 묻는다.
fn read<P: Parser>(p: &P, text: &str) -> Result<P::Output, String> {
    if text.len() > P::MAX_LEN {
        return Err(format!("{}: 너무 길다", P::NAME));
    }
    p.parse(text).ok_or(format!("{} 아님: {text}", P::NAME))
}

fn main() {
    println!("{:?}", read(&Int, "42"));
    println!("{:?}", read(&Int, "4x"));
    println!("{:?}", read(&Flag, "false"));
    println!("{:?}", read(&Flag, "maybe"));
    println!("{:?}", read(&Flag, "perhaps"));
}
