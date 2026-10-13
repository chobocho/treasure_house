// title 이 prefix 로 시작하면 그 뒤를, 아니면 title 전체를 돌려준다.
fn strip(title: &str, prefix: &str) -> &str {
    title.strip_prefix(prefix).unwrap_or(title)
}

fn main() {
    let title = String::from("Re: Fwd: 회의 시간");
    let mut rest = title.as_str();
    for tag in ["Re", "Fwd", "Re"] {
        // prefix 는 이 바퀴가 끝나면 사라진다.
        let prefix = format!("{tag}: ");
        rest = strip(rest, &prefix);
        println!("{prefix:<5} 뗀 뒤 [{rest}]");
    }
    println!("남은 제목 [{rest}]");
}
//@ expect: E0106
