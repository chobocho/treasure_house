// "이름=숫자" 줄들을 읽는다. 어느 줄이 왜 틀렸는지 알려 준다.
fn parse_line(no: usize, line: &str) -> Result<(String, u32), String> {
    let (key, value) = line
        .split_once('=')
        .ok_or(format!("{no}번째 줄: `=` 가 없다"))?;
    let n = value.trim().parse::<u32>().map_err(|e| {
        format!("{no}번째 줄: `{}` — {e}", value.trim())
    })?;
    Ok((key.trim().to_string(), n))
}

fn main() {
    let text = "width = 80\nheight 24\ndepth = -1\ntabs = 4";
    for (i, line) in text.lines().enumerate() {
        match parse_line(i + 1, line) {
            Ok((k, v)) => println!("{k} → {v}"),
            Err(e) => println!("오류 — {e}"),
        }
    }
}
