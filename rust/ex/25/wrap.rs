// text 의 낱말을 줄마다 width 글자까지 채워 넣는다
fn wrap(text: &str, width: usize) -> Vec<String> {
    let mut lines = Vec::new();
    let mut line = String::new();
    for word in text.split_whitespace() {
        // 빈칸 하나와 이 낱말을 더했을 때의 글자 수
        let need = line.chars().count() + 1 + word.chars().count();
        if !line.is_empty() && need > width {
            lines.push(line);
            line = String::new();
        }
        if !line.is_empty() {
            line.push(' ');
        }
        line.push_str(word);
    }
    if !line.is_empty() {
        lines.push(line);
    }
    lines
}

fn main() {
    let text = "seven eleven one two three extraordinarily so  on";
    let lines = wrap(text, 12);
    println!("{}줄", lines.len());
    for line in &lines {
        println!("|{line:<12}|");
    }
    println!("{}줄", wrap("   ", 12).len());
}
