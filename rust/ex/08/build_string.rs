fn main() {
    let items = ["사과", "배", "감"];

    // 손으로 — 구분자를 언제 넣을지 직접 챙긴다.
    let mut a = String::new();
    for (i, item) in items.iter().enumerate() {
        if i > 0 {
            a.push_str(", ");
        }
        a.push_str(item);
    }
    // join — 같은 일을 한 줄로.
    let b = items.join(", ");
    // 바꾸면서 모으기.
    let c: Vec<String> =
        items.iter().map(|s| format!("[{s}]")).collect();
    println!("{a}\n{b}\n{}", c.concat());
}
