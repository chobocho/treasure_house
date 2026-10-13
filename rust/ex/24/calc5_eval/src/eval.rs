use crate::error::{CalcError, Kind};
use crate::expr::{Expr, Op};

// 두 수에 연산 하나를 한다. 실패하면 그 종류만 돌려준다.
// 자리는 나무를 쥔 eval 이 붙인다
pub fn apply(op: Op, a: i64, b: i64) -> Result<i64, Kind> {
    let value = match op {
        Op::Add => a.checked_add(b),
        Op::Sub => a.checked_sub(b),
        Op::Mul => a.checked_mul(b),
        // checked_div 는 0 으로 나눌 때도 넘칠 때도 None 이다.
        // 둘을 가르려고 0 을 먼저 본다
        Op::Div if b == 0 => return Err(Kind::DivByZero),
        Op::Div => a.checked_div(b),
    };
    value.ok_or(Kind::Overflow)
}

// 나무를 따라 내려가며 값을 구한다
pub fn eval(expr: &Expr) -> Result<i64, CalcError> {
    match expr {
        Expr::Num(n) => Ok(*n),
        Expr::Neg(pos, inner) => {
            let value = eval(inner)?;
            value
                .checked_neg()
                .ok_or(CalcError::new(Kind::Overflow, *pos))
        }
        Expr::Bin(left, op, pos, right) => {
            // 왼쪽을 먼저 구한다
            let a = eval(left)?;
            let b = eval(right)?;
            apply(*op, a, b).map_err(|kind| CalcError::new(kind, *pos))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse::parse;
    use crate::token::tokenize;

    // 줄 하나를 값까지 가져간다
    fn value(line: &str) -> Result<i64, CalcError> {
        eval(&parse(&tokenize(line)?)?)
    }

    fn err<T>(kind: Kind, pos: usize) -> Result<T, CalcError> {
        Err(CalcError::new(kind, pos))
    }

    #[test]
    fn shape_of_the_tree_decides_the_value() {
        assert_eq!(value("2 + 3 * 4"), Ok(14));
        assert_eq!(value("(2 + 3) * 4"), Ok(20));
        // 왼쪽부터 묶어 (8 - 3) - 2. 오른쪽부터였다면 7 이다
        assert_eq!(value("8 - 3 - 2"), Ok(3));
        assert_eq!(value("8 - (3 - 2)"), Ok(7));
        assert_eq!(value("8 / 4 / 2"), Ok(1));
        assert_eq!(value("--3"), Ok(3));
        assert_eq!(value("2 - -3"), Ok(5));
        assert_eq!(value("007"), Ok(7));
    }

    #[test]
    fn division_drops_the_fraction() {
        assert_eq!(value("7 / 2"), Ok(3));
        // 0 쪽으로 버린다. 작은 쪽으로 내렸다면 -4 다
        assert_eq!(value("-7 / 2"), Ok(-3));
        assert_eq!(value("7 / -2"), Ok(-3));
        assert_eq!(value("-7 / -2"), Ok(3));
        assert_eq!(value("1 / 2 * 2"), Ok(0));
    }

    #[test]
    fn apply_tells_zero_from_overflow() {
        assert_eq!(apply(Op::Div, 1, 0), Err(Kind::DivByZero));
        assert_eq!(apply(Op::Div, 0, 0), Err(Kind::DivByZero));
        // 표준 라이브러리는 두 경우 모두 None 을 준다
        assert_eq!(1_i64.checked_div(0), None);
        assert_eq!(i64::MIN.checked_div(-1), None);
        assert_eq!(apply(Op::Div, i64::MIN, -1), Err(Kind::Overflow));
        assert_eq!(apply(Op::Add, i64::MAX, 1), Err(Kind::Overflow));
        assert_eq!(apply(Op::Sub, i64::MIN, 1), Err(Kind::Overflow));
        assert_eq!(apply(Op::Mul, i64::MAX, 2), Err(Kind::Overflow));
        // 끝값에 닿는 것까지는 된다
        assert_eq!(apply(Op::Add, i64::MAX - 1, 1), Ok(i64::MAX));
        assert_eq!(apply(Op::Mul, i64::MIN, 1), Ok(i64::MIN));
    }

    #[test]
    fn errors_point_at_the_operator() {
        assert_eq!(value("1 + 2 / 0"), err(Kind::DivByZero, 6));
        assert_eq!(value("0 / 0"), err(Kind::DivByZero, 2));
        assert_eq!(
            value("9223372036854775807 + 1"),
            err(Kind::Overflow, 20)
        );
        // 둘 다 틀렸으면 왼쪽 것이 나온다
        let line = "1 / 0 + 9223372036854775807 * 2";
        assert_eq!(value(line), err(Kind::DivByZero, 2));
        let line = "9223372036854775807 * 2 + 1 / 0";
        assert_eq!(value(line), err(Kind::Overflow, 20));
    }

    #[test]
    fn smallest_number_cannot_be_written_as_one_literal() {
        // - 가 붙기 전에 숫자들이 먼저 수가 되는데, 그 수가 i64 에 없다
        assert_eq!(value("-9223372036854775808"), err(Kind::TooBig, 1));
        assert_eq!(value("-9223372036854775807 - 1"), Ok(i64::MIN));
        // 그 수의 부호를 바꾼 값도, -1 로 나눈 값도 i64 에 없다
        let line = "-(-9223372036854775807 - 1)";
        assert_eq!(value(line), err(Kind::Overflow, 0));
        let line = "(-9223372036854775807 - 1) / -1";
        assert_eq!(value(line), err(Kind::Overflow, 27));
    }
}
