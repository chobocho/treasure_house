// 입력 하나에서 센 것. 찍는 차례도 이 차례다
pub struct Counts {
    pub lines: usize,
    pub words: usize,
    pub chars: usize,
    pub bytes: usize,
}

// 바이트 슬라이스 하나를 센다. 어디서 온 바이트인지는 모른다
pub fn count(bytes: &[u8]) -> Counts {
    Counts {
        // 줄: 줄바꿈 바이트의 수
        lines: bytes.iter().filter(|&&b| b == b'\n').count(),
        // 낱말: ASCII 공백에서 갈라 남는, 비지 않은 조각의 수
        words: bytes
            .split(|b| b.is_ascii_whitespace())
            .filter(|w| !w.is_empty())
            .count(),
        // 글자: 글로 읽히지 않는 바이트는 U+FFFD 로 바꿔 센다
        chars: String::from_utf8_lossy(bytes).chars().count(),
        bytes: bytes.len(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn line_is_a_newline_byte() {
        assert_eq!(count(b"a\nb\n").lines, 2);
        // 줄바꿈 없이 끝난 마지막 줄은 세지 않는다
        assert_eq!(count(b"a\nb").lines, 1);
        assert_eq!(count(b"").lines, 0);
    }

    #[test]
    fn word_is_a_run_between_ascii_spaces() {
        assert_eq!(count(b"  one two\n\nthree  ").words, 3);
        // 탭 · CR · 쪽 넘김(\x0c)도 가른다
        assert_eq!(count(b"a\tb\rc\x0cd").words, 4);
        // 세로 탭(\x0b)은 ASCII 공백으로 치지 않는다
        assert_eq!(count(b"a\x0bb").words, 1);
        assert_eq!(count(b" \n\t").words, 0);
        // split 만으로는 빈칸 둘 사이의 빈 조각도 나온다
        let pieces = b"a  b".split(|b| b.is_ascii_whitespace());
        assert_eq!(pieces.count(), 3);
    }

    #[test]
    fn bytes_is_the_length() {
        assert_eq!(count(b"a b\n").bytes, 4);
        assert_eq!(count("가 나\n".as_bytes()).bytes, 8);
    }

    #[test]
    fn unicode_space_does_not_split() {
        // U+3000 은 전각 빈칸이다. ASCII 가 아니다
        let text = "가\u{3000}나";
        assert_eq!(count(text.as_bytes()).words, 1);
        // str 의 split_whitespace 는 같은 글을 둘로 가른다
        assert_eq!(text.split_whitespace().count(), 2);
    }

    #[test]
    fn chars_are_fewer_than_bytes_in_korean() {
        let c = count("가 나\n".as_bytes());
        assert_eq!((c.chars, c.bytes), (4, 8));
        // ASCII 뿐이면 둘이 같다
        let c = count(b"a b\n");
        assert_eq!((c.chars, c.bytes), (4, 4));
    }

    #[test]
    fn broken_bytes_become_replacement_chars() {
        // \xff 와 \xfe 는 UTF-8 어디에도 나올 수 없는 바이트다
        assert_eq!(count(b"ok\xff\xfe").chars, 4);
        // '가' 의 세 바이트 가운데 앞의 둘만 있다
        let cut = &"가".as_bytes()[..2];
        assert_eq!(count(cut).chars, 1);
        let seen = String::from_utf8_lossy(cut);
        assert_eq!(seen, "\u{FFFD}");
    }
}
