// 끝의 keep 바이트를 빌려서 돌려준다. 그보다 짧으면 전체다.
fn tail(card: &str, keep: usize) -> &str {
    if card.len() <= keep {
        return card;
    }
    &card[card.len() - keep..]
}

// 끝의 keep 바이트와 - 는 그대로 두고 나머지를 * 로 바꾼 새 글
fn masked(card: &str, keep: usize) -> String {
    let shown = tail(card, keep);
    let hidden = &card[..card.len() - shown.len()];
    let bytes = hidden.as_bytes();
    let mut out = String::new();
    for i in 0..bytes.len() {
        if bytes[i] == b'-' {
            out.push_str("-");
        } else {
            out.push_str("*");
        }
    }
    out.push_str(shown);
    out
}

fn main() {
    let card = String::from("1234-5678-9012-3456");
    let hidden = masked(&card, 4);
    println!("{card} -> {hidden}");
    println!("끝 네 자리 {}", tail(&card, 4));
    println!("{} {}", masked("010-1234-5678", 4), masked("77", 4));
}
