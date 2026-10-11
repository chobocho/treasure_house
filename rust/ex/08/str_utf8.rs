fn main() {
    for s in ["abc", "가나다", "a가🦀"] {
        // len 은 글자 수가 아니라 바이트 수다.
        println!(
            "{s:?}: {} 바이트, {} 글자",
            s.len(),
            s.chars().count()
        );
    }
}
