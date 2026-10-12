// 줄마다 양쪽에 칸을 붙였다가, pick 이 고른 조각을 찍는다.
fn each_line<'a, F>(text: &str, pick: F)
where
    F: Fn(&'a str) -> &'a str,
{
    for line in text.lines() {
        let padded = format!("  {line}  ");
        println!("[{}]", pick(&padded));
    }
}

fn main() {
    each_line("ab cd\nef", |s| s.trim());
}
//@ expect: E0597
