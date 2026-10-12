// 글 한 조각을 값으로 읽는 것들. 돌려주는 타입은 구현마다 다르다.
trait Parser {
    type Output;

    fn parse(&self, text: &str) -> Option<Self::Output>;
}

struct Int;
struct Flag;

impl Parser for Int {
    type Output = i64;

    fn parse(&self, text: &str) -> Option<i64> {
        text.trim().parse().ok()
    }
}

impl Parser for Flag {
    type Output = bool;

    fn parse(&self, text: &str) -> Option<bool> {
        match text.trim() {
            "on" => Some(true),
            "off" => Some(false),
            _ => None,
        }
    }
}

// 어떤 Parser 든 받는다. 돌려주는 타입은 P 를 따라간다.
fn parse_all<P: Parser>(
    p: &P,
    texts: &[&str],
) -> Vec<Option<P::Output>> {
    texts.iter().map(|t| p.parse(t)).collect()
}

fn main() {
    let nums = parse_all(&Int, &["42", " -7 ", "x"]);
    let flags = parse_all(&Flag, &["on", "off", "maybe"]);
    println!("{nums:?}");
    println!("{flags:?}");
}
