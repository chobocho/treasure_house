// 어떤 수명 'a 를 넣어도 성립하는 F 여야 한다.
fn each_line<F>(text: &str, pick: F)
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    for line in text.lines() {
        let padded = format!("  {line}  ");
        println!("[{}]", pick(&padded));
    }
}

fn first_word(s: &str) -> &str {
    s.split_whitespace().next().unwrap_or("")
}

fn main() {
    each_line("ab cd\nef", |s| s.trim());
    each_line("ab cd\nef", first_word);
}
