// 두 값 사이에 놓이는 연산
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Op {
    Add,
    Sub,
    Mul,
    Div,
}

// 식의 나무. 연산자가 있던 자리도 마디에 담아 둔다.
// 계산하다 난 오류가 줄의 어디인지 말하려는 것이다
#[derive(Debug, PartialEq)]
pub enum Expr {
    // 수 하나
    Num(i64),
    // 부호 - 의 자리, 그리고 부호가 붙은 식
    Neg(usize, Box<Expr>),
    // 왼쪽 식, 연산, 연산자의 자리, 오른쪽 식
    Bin(Box<Expr>, Op, usize, Box<Expr>),
}
