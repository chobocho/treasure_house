/// 이름과 수를 한 줄에 하나씩 적은 표를 만든다.
pub fn render(rows: &[(&str, u32)]) -> String {
    let mut text = String::new();
    for (name, n) in rows {
        text.push_str(&format!("{name:<6}{n:>4}\n"));
    }
    text
}
