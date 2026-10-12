// 수명을 적지 않은 조건
fn each_short<F: Fn(&str) -> &str>(text: &str, pick: F) {
    for line in text.lines() {
        let padded = format!("  {line}  ");
        println!("[{}]", pick(&padded));
    }
}

// for<'a> 로 다 적은 조건. 받은 것을 each_short 에 넘긴다.
fn each_long<F>(text: &str, pick: F)
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    each_short(text, pick);
}

// 거꾸로, 짧게 적은 조건으로 받아 each_long 에 넘긴다.
fn each_back<F: Fn(&str) -> &str>(text: &str, pick: F) {
    each_long(text, pick);
}

fn main() {
    each_long("ab cd\nef", |s| s.trim());
    each_back("gh", |s| s.trim());
}
