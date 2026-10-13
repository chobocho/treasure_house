mod error;
mod eval;
mod expr;
mod parse;
mod token;

pub use error::{CalcError, Kind, caret_line, report};
pub use eval::{apply, eval};
pub use expr::{Expr, Op};
pub use parse::{MAX_TOKENS, parse};
pub use token::{Token, tokenize};

// 줄 하나를 값으로 바꾼다. 세 함수가 같은 오류 타입을 써서
// ? 가 그대로 올려 보낸다. 토큰이 없는 줄에는 값이 없다
pub fn calc(line: &str) -> Result<Option<i64>, CalcError> {
    let tokens = tokenize(line)?;
    // 빈 줄의 토큰 목록은 End 하나다
    if tokens.len() <= 1 {
        return Ok(None);
    }
    let tree = parse(&tokens)?;
    let value = eval(&tree)?;
    Ok(Some(value))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn err<T>(kind: Kind, pos: usize) -> Result<T, CalcError> {
        Err(CalcError::new(kind, pos))
    }

    #[test]
    fn calc_goes_through_three_stages() {
        assert_eq!(calc("2 + 3 * 4"), Ok(Some(14)));
        // 함수마다 하나씩 — tokenize, parse, eval 에서 난 오류
        assert_eq!(calc("2 + 3 * 가"), err(Kind::UnknownChar, 8));
        assert_eq!(calc("2 + 3 *"), err(Kind::Ended, 7));
        assert_eq!(calc("2 + 3 / 0"), err(Kind::DivByZero, 6));
    }

    #[test]
    fn line_without_tokens_has_no_value() {
        assert_eq!(calc(""), Ok(None));
        assert_eq!(calc(" \t "), Ok(None));
        // 전각 빈칸은 빈칸이 아니라 모르는 글자다
        assert_eq!(calc("\u{3000}"), err(Kind::UnknownChar, 0));
    }
}
