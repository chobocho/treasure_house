// 줄이 패턴을 품었는가. 패턴은 글자 그대로 찾는 글이다
pub fn is_match(line: &str, pattern: &str) -> bool {
    line.contains(pattern)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pattern_is_found_as_plain_text() {
        assert!(is_match("녹은 영어로 rust 다", "rust"));
        // 낱말의 한가운데에 있어도 맞는다
        assert!(is_match("trust", "rust"));
        // 대소문자가 다르면 다른 글이다
        assert!(!is_match("Rust book 을 샀다", "rust"));
        // 특별한 뜻을 가진 글자는 없다. 점은 점만 찾는다
        assert!(is_match("a.c", "."));
        assert!(!is_match("abc", "a.c"));
    }

    #[test]
    fn hangul_is_compared_char_by_char() {
        assert!(is_match("쇠는 비를 맞으면 녹이 슨다", "녹이"));
        // 자모 둘(U+1100 U+1161)로 적은 "가" 는
        // 한 글자 "가"(U+AC00) 와 다른 글이다
        assert!(!is_match("\u{1100}\u{1161}", "\u{AC00}"));
    }

    #[test]
    fn empty_pattern_is_in_every_line() {
        assert!(is_match("abc", ""));
        assert!(is_match("", ""));
        // 빈 줄에 맞는 것은 빈 패턴뿐이다
        assert!(!is_match("", "a"));
    }
}
