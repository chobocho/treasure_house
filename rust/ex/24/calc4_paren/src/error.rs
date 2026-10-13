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
