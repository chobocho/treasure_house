use crate::error::{CalcError, Kind};

// 식을 이루는 낱개. End 는 줄이 끝난 자리를 나타낸다
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Token {
    Num(i64),
    Plus,
    Minus,
    Star,
    Slash,
    LParen,
    RParen,
    End,
}

// 읽던 수 뒤에 숫자 하나를 붙인다. i64 를 넘으면 None 이다
fn push_digit(value: i64, digit: u32) -> Option<i64> {
    value.checked_mul(10)?.checked_add(i64::from(digit))
}

// 줄을 토큰과 그 자리의 목록으로 바꾼다.
// 자리는 줄의 처음부터 센 바이트 번호다
pub fn tokenize(line: &str) -> Result<Vec<(Token, usize)>, CalcError> {
    let mut tokens = Vec::new();
    let mut chars = line.char_indices().peekable();
    while let Some((pos, c)) = chars.next() {
        let token = if let Some(first) = c.to_digit(10) {
            // 숫자가 이어지는 데까지가 수 하나다
            let mut value = i64::from(first);
            while let Some(&(_, next)) = chars.peek() {
                let Some(digit) = next.to_digit(10) else {
                    break;
                };
                chars.next();
                value = push_digit(value, digit)
                    .ok_or(CalcError::new(Kind::TooBig, pos))?;
            }
            Token::Num(value)
        } else {
            match c {
                // 토큰 사이를 띄우는 것은 빈칸과 탭 둘뿐이다
                ' ' | '\t' => continue,
                '+' => Token::Plus,
                '-' => Token::Minus,
                '*' => Token::Star,
                '/' => Token::Slash,
                '(' => Token::LParen,
                ')' => Token::RParen,
                _ => {
                    return Err(CalcError::new(Kind::UnknownChar, pos));
                }
            }
        };
        tokens.push((token, pos));
    }
    // 줄의 길이가 End 의 자리다
    tokens.push((Token::End, line.len()));
    Ok(tokens)
}

#[cfg(test)]
mod tests {
    use super::*;
    use Token::*;

    fn err<T>(kind: Kind, pos: usize) -> Result<T, CalcError> {
        Err(CalcError::new(kind, pos))
    }

    #[test]
    fn tokens_carry_their_positions() {
        let want = vec![(Num(12), 0), (Plus, 3), (Num(3), 5), (End, 6)];
        assert_eq!(tokenize("12 + 3"), Ok(want));
        // 붙여 써도 토큰은 따로다
        let want = vec![
            (LParen, 0),
            (Num(4), 1),
            (Minus, 2),
            (Num(5), 3),
            (RParen, 4),
            (Star, 5),
            (Num(6), 6),
            (Slash, 7),
            (Num(7), 8),
            (End, 9),
        ];
        assert_eq!(tokenize("(4-5)*6/7"), Ok(want));
    }

    #[test]
    fn blank_line_is_end_alone() {
        assert_eq!(tokenize(""), Ok(vec![(End, 0)]));
        assert_eq!(tokenize(" \t "), Ok(vec![(End, 3)]));
    }

    #[test]
    fn number_is_a_run_of_ascii_digits() {
        // 앞의 0 은 그대로 읽는다
        assert_eq!(tokenize("007"), Ok(vec![(Num(7), 0), (End, 3)]));
        // 밑줄과 점은 수의 일부가 아니다
        assert_eq!(tokenize("1_000"), err(Kind::UnknownChar, 1));
        assert_eq!(tokenize("1.5"), err(Kind::UnknownChar, 1));
        // ASCII 표에서 9 바로 다음 글자는 콜론이다
        assert_eq!(char::from(b'9' + 1), ':');
        assert_eq!(tokenize("9:"), err(Kind::UnknownChar, 1));
        // 전각 숫자 3 과 아라비아 문자의 숫자 3. 유니코드는 숫자로
        // 치지만, 0 부터 9 가 아니면 이 프로그램은 모른다
        for c in ['３', '\u{663}'] {
            assert!(c.is_numeric());
            assert_eq!(c.to_digit(10), None);
            assert_eq!(
                tokenize(&c.to_string()),
                err(Kind::UnknownChar, 0)
            );
        }
    }

    #[test]
    fn number_must_fit_in_i64() {
        assert_eq!(push_digit(922337203685477580, 7), Some(i64::MAX));
        assert_eq!(push_digit(922337203685477580, 8), None);
        assert_eq!(push_digit(i64::MAX, 0), None);
        let max = vec![(Num(i64::MAX), 0), (End, 19)];
        assert_eq!(tokenize("9223372036854775807"), Ok(max));
        assert_eq!(
            tokenize("9223372036854775808"),
            err(Kind::TooBig, 0)
        );
        // 자리는 넘친 숫자가 아니라 수가 시작한 곳이다
        let line = "1 + 123456789012345678901234567890";
        assert_eq!(tokenize(line), err(Kind::TooBig, 4));
    }

    #[test]
    fn only_space_and_tab_separate_tokens() {
        let want = vec![(Num(1), 1), (Plus, 3), (Num(2), 5), (End, 7)];
        assert_eq!(tokenize(" 1\t+ 2 "), Ok(want));
        // 전각 빈칸, 줄바꿈 없는 빈칸, CR 은 모르는 글자다
        for c in ['\u{3000}', '\u{a0}', '\r'] {
            assert!(c.is_whitespace());
            let line = format!("1{c}2");
            assert_eq!(tokenize(&line), err(Kind::UnknownChar, 1));
        }
    }

    #[test]
    fn position_has_only_ascii_before_it() {
        assert_eq!(tokenize("1 + 가"), err(Kind::UnknownChar, 4));
        assert_eq!(tokenize("(가)"), err(Kind::UnknownChar, 1));
        // 모르는 글자가 여럿이어도 알리는 것은 첫째다
        for line in ["가 + 나", "12 * 가 - 나", "1 + ３"] {
            let e = tokenize(line).unwrap_err();
            assert!(line[..e.pos].is_ascii());
        }
    }
}
