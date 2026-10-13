use std::fmt;

// 줄을 항목으로 읽지 못한 까닭
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum LineError {
    // 키와 값을 가르는 탭이 없다
    NoTab,
    // 역슬래시 다음이 \ · t · n · r 이 아니다
    BadEscape,
}

impl fmt::Display for LineError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let why = match self {
            LineError::NoTab => "탭이 없다",
            LineError::BadEscape => "모르는 이스케이프다",
        };
        write!(f, "{why}")
    }
}

// 글을 한 줄 안에 적을 수 있게 바꾼다. 역슬래시 · 탭 · 줄바꿈 · CR
// 넷을 역슬래시로 시작하는 두 글자로 적는다
pub fn escape(text: &str) -> String {
    let mut out = String::new();
    for c in text.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '\t' => out.push_str("\\t"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            _ => out.push(c),
        }
    }
    out
}

// escape 가 바꾼 글을 되돌린다
pub fn unescape(text: &str) -> Result<String, LineError> {
    let mut out = String::new();
    let mut chars = text.chars();
    while let Some(c) = chars.next() {
        if c != '\\' {
            out.push(c);
            continue;
        }
        // 역슬래시 다음 글자가 무엇을 적은 것인지 가른다
        match chars.next() {
            Some('\\') => out.push('\\'),
            Some('t') => out.push('\t'),
            Some('n') => out.push('\n'),
            Some('r') => out.push('\r'),
            _ => return Err(LineError::BadEscape),
        }
    }
    Ok(out)
}

// 항목 하나를 한 줄로 적는다. 줄바꿈은 붙이지 않는다
pub fn encode(key: &str, value: &str) -> String {
    format!("{}\t{}", escape(key), escape(value))
}

// 한 줄을 항목으로 읽는다. 첫 탭이 키와 값을 가른다
pub fn decode(line: &str) -> Result<(String, String), LineError> {
    let (key, value) = line.split_once('\t').ok_or(LineError::NoTab)?;
    Ok((unescape(key)?, unescape(value)?))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pair(
        key: &str,
        value: &str,
    ) -> Result<(String, String), LineError> {
        Ok((key.to_string(), value.to_string()))
    }

    #[test]
    fn four_characters_are_escaped() {
        assert_eq!(escape("a\\b"), "a\\\\b");
        assert_eq!(escape("a\tb\nc\rd"), "a\\tb\\nc\\rd");
        // 그 넷이 아니면 그대로다 — 빈칸, 한글, NUL
        assert_eq!(escape("a b 가\0"), "a b 가\0");
        assert_eq!(encode("name", "보리 차"), "name\t보리 차");
        assert_eq!(encode("", ""), "\t");
        assert_eq!(encode("k\tk", "v\tv"), "k\\tk\tv\\tv");
    }

    #[test]
    fn decode_splits_at_the_first_tab() {
        assert_eq!(decode("name\t보리 차"), pair("name", "보리 차"));
        assert_eq!(decode("\t"), pair("", ""));
        assert_eq!(decode("k\\tk\tv\\tv"), pair("k\tk", "v\tv"));
        // 값 쪽에 남은 날 탭은 값의 글자다
        assert_eq!(decode("a\tb\tc"), pair("a", "b\tc"));
    }

    #[test]
    fn broken_lines_are_errors() {
        assert_eq!(decode("name 보리"), Err(LineError::NoTab));
        assert_eq!(decode(""), Err(LineError::NoTab));
        assert_eq!(decode("a\tb\\x"), Err(LineError::BadEscape));
        // 대문자 T 는 t 가 아니다
        assert_eq!(decode("a\tb\\T"), Err(LineError::BadEscape));
        // 줄 끝에 홀로 남은 역슬래시도 같다
        assert_eq!(decode("a\tb\\"), Err(LineError::BadEscape));
        // 키 쪽이 틀려도 같다
        assert_eq!(decode("a\\q\tb"), Err(LineError::BadEscape));
        assert_eq!(LineError::NoTab.to_string(), "탭이 없다");
        assert_eq!(
            LineError::BadEscape.to_string(),
            "모르는 이스케이프다"
        );
    }

    #[test]
    fn every_pair_comes_back() {
        let awkward = [
            "",
            " ",
            "a b",
            "\t",
            "\n",
            "\r",
            "a\r\n",
            "\\",
            "\\t",
            "\\\\n",
            "끝\\",
            "\0",
            "가\t나\n다",
        ];
        for key in &awkward {
            for value in &awkward {
                let line = encode(key, value);
                // 한 줄이다. 줄을 가르는 글자가 없고 탭은 하나뿐이다
                assert!(!line.contains('\n') && !line.contains('\r'));
                assert_eq!(line.matches('\t').count(), 1);
                assert_eq!(decode(&line), pair(key, value));
            }
        }
    }

    #[test]
    fn cr_is_escaped_so_that_lines_keeps_it() {
        // CR 로 끝나는 값을 바꾸지 않고 줄로 적었다면,
        // lines() 가 \r\n 을 함께 떼어 CR 이 사라진다
        assert_eq!("a\tb\r\n".lines().next(), Some("a\tb"));
        // 바꿔 적은 줄에서는 남는다
        let text = format!("{}\n", encode("a", "b\r"));
        assert_eq!(text, "a\tb\\r\n");
        let line = text.lines().next().unwrap_or("");
        assert_eq!(decode(line), pair("a", "b\r"));
    }
}
