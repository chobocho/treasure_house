fn shout(text: &str) -> String {
    // 같은 이름으로 다시 묶는다 — 다듬은 값만 남기는 관용구.
    let text = text.trim();
    let text = text.to_uppercase();
    format!("{text}!")
}

fn main() {
    println!("{}", shout("  hello  "));
}
