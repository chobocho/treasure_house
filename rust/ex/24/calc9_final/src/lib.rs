use std::io::{self, BufRead, BufReader, Read, Write};

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

// 줄 하나에 답한다. 값은 out 에, 알림은 err 에 쓴다.
// 돌려주는 값은 "그 줄이 오류였는가" 다
fn answer(
    line: &str,
    out: &mut impl Write,
    err: &mut impl Write,
) -> io::Result<bool> {
    match calc(line) {
        Ok(Some(value)) => {
            writeln!(out, "{value}")?;
            Ok(false)
        }
        // 계산할 것이 없는 줄에는 아무것도 쓰지 않는다
        Ok(None) => Ok(false),
        Err(e) => {
            writeln!(err, "{}", report(line, &e))?;
            Ok(true)
        }
    }
}

// 오류였던 줄이 하나라도 있으면 1 이다
pub fn exit_code(failed: bool) -> u8 {
    if failed { 1 } else { 0 }
}

pub fn run(
    args: &[String],
    stdin: impl Read,
    out: &mut impl Write,
    err: &mut impl Write,
) -> io::Result<u8> {
    let mut failed = false;
    if args.is_empty() {
        // 인자가 없으면 표준 입력의 줄마다 답한다
        for line in BufReader::new(stdin).lines() {
            let line = line?;
            if answer(&line, out, err)? {
                failed = true;
            }
        }
    } else {
        // 인자가 있으면 인자가 식이다. 인자도 줄로 쪼개 본다
        for arg in args {
            for line in arg.lines() {
                if answer(line, out, err)? {
                    failed = true;
                }
            }
        }
    }
    Ok(exit_code(failed))
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

    #[test]
    fn exit_code_is_one_after_any_error() {
        assert_eq!(exit_code(false), 0);
        assert_eq!(exit_code(true), 1);
    }
}
