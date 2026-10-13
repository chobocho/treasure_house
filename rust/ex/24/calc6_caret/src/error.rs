use std::fmt;

// 오류의 종류. 어디서 났는지는 CalcError 의 pos 가 맡는다
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Kind {
    // 토큰이 될 수 없는 글자
    UnknownChar,
    // i64 에 담을 수 없는 수
    TooBig,
    // 인수가 올 자리에서 줄이 끝났다
    Ended,
    // 인수가 올 자리에 다른 토큰이 있다
    NotOperand,
    // 식이 끝난 자리에 토큰이 더 있다
    Trailing,
    // 여는 괄호의 짝이 없다
    Unclosed,
    // 나누는 수가 0 이다
    DivByZero,
    // 계산한 값이 i64 를 넘었다
    Overflow,
}

// 종류와 자리. 자리는 받은 줄의 처음부터 센 바이트 번호다
#[derive(Debug, PartialEq)]
pub struct CalcError {
    pub kind: Kind,
    pub pos: usize,
}

impl CalcError {
    pub fn new(kind: Kind, pos: usize) -> Self {
        CalcError { kind, pos }
    }
}

impl fmt::Display for CalcError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let why = match self.kind {
            Kind::UnknownChar => "모르는 글자",
            Kind::TooBig => "수가 너무 크다",
            Kind::Ended => "수나 괄호가 올 자리에서 줄이 끝났다",
            Kind::NotOperand => "수나 괄호가 올 자리다",
            Kind::Trailing => "식이 끝난 자리에 남은 것이 있다",
            Kind::Unclosed => "괄호가 닫히지 않았다",
            Kind::DivByZero => "0 으로 나눌 수 없다",
            Kind::Overflow => "값이 i64 를 넘었다",
        };
        write!(f, "{why} (자리 {})", self.pos)
    }
}

impl std::error::Error for CalcError {}

// 오류가 난 자리 아래에 ^ 를 놓은 줄을 만든다.
// 그 앞의 글자는 빈칸으로, 탭은 탭 그대로 옮긴다
pub fn caret_line(line: &str, pos: usize) -> String {
    // 자리가 글자 경계가 아니거나 줄보다 길면 줄 전체를 쓴다
    let before = line.get(..pos).unwrap_or(line);
    let mut out: String = before
        .chars()
        .map(|c| if c == '\t' { '\t' } else { ' ' })
        .collect();
    out.push('^');
    out
}

// 알림 석 줄 — 까닭, 받은 줄, 자리를 짚는 줄
pub fn report(line: &str, e: &CalcError) -> String {
    format!("calc: {e}\n{line}\n{}", caret_line(line, e.pos))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn display_is_reason_and_position() {
        let e = CalcError::new(Kind::DivByZero, 6);
        assert_eq!(e.to_string(), "0 으로 나눌 수 없다 (자리 6)");
        let e = CalcError::new(Kind::Unclosed, 0);
        assert_eq!(e.to_string(), "괄호가 닫히지 않았다 (자리 0)");
        // Error 를 구현했으므로 Box<dyn Error> 에 들어간다
        let boxed: Box<dyn std::error::Error> = Box::new(e);
        assert_eq!(boxed.to_string(), "괄호가 닫히지 않았다 (자리 0)");
    }

    #[test]
    fn caret_sits_under_the_position() {
        assert_eq!(caret_line("1 / 0", 2), "  ^");
        assert_eq!(caret_line("1 +", 3), "   ^");
        assert_eq!(caret_line("+ 1", 0), "^");
        // 한글 앞까지는 ASCII 뿐이라 바이트 수가 곧 칸 수다
        assert_eq!(caret_line("1 + 가", 4), "    ^");
        assert_eq!(caret_line("(가)", 1), " ^");
        // 탭은 탭 그대로다. 화면이 탭을 몇 칸으로 그릴지 모른다
        assert_eq!(caret_line("1\t+ )", 4), " \t  ^");
    }

    #[test]
    fn caret_never_panics_on_a_bad_position() {
        // 줄보다 긴 자리, 글자 한가운데의 자리
        assert_eq!(caret_line("ab", 9), "  ^");
        assert_eq!(caret_line("가", 1), " ^");
    }

    #[test]
    fn report_is_three_lines() {
        let e = CalcError::new(Kind::UnknownChar, 4);
        let want = "calc: 모르는 글자 (자리 4)\n1 + 가\n    ^";
        assert_eq!(report("1 + 가", &e), want);
    }
}
