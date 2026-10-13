use crate::error::{CalcError, Kind};
use crate::expr::{Expr, Op};
use crate::token::Token;

// 한 줄에 받는 토큰의 수. End 는 세지 않는다
pub const MAX_TOKENS: usize = 200;

// 토큰 목록 전체를 식 하나로 읽는다
pub fn parse(tokens: &[(Token, usize)]) -> Result<Expr, CalcError> {
    // 재귀의 깊이는 토큰의 수를 넘지 못한다. 그 수를 먼저 막는다
    match tokens.get(MAX_TOKENS) {
        Some(&(token, pos)) if token != Token::End => {
            return Err(CalcError::new(Kind::TooLong, pos));
        }
        _ => {}
    }
    let mut parser = Parser { tokens, i: 0 };
    let expr = parser.parse_expr()?;
    // 식을 다 읽었으면 남은 것은 End 뿐이어야 한다
    match parser.peek() {
        (Token::End, _) => Ok(expr),
        (_, pos) => Err(CalcError::new(Kind::Trailing, pos)),
    }
}

// 읽을 목록과, 지금 볼 토큰의 인덱스
struct Parser<'a> {
    tokens: &'a [(Token, usize)],
    i: usize,
}

impl<'a> Parser<'a> {
    // 지금 볼 토큰과 그 자리. 넘어가지는 않는다
    fn peek(&self) -> (Token, usize) {
        match self.tokens.get(self.i) {
            Some(&pair) => pair,
            // tokenize 가 만든 목록은 End 로 끝나서 여기로 오지 않는다
            None => (Token::End, 0),
        }
    }

    // 지금 볼 토큰을 돌려주고 다음으로 넘어간다. End 는 넘지 않는다
    fn next(&mut self) -> (Token, usize) {
        let pair = self.peek();
        if pair.0 != Token::End {
            self.i += 1;
        }
        pair
    }

    // 식 = 항 { ("+" | "-") 항 }
    fn parse_expr(&mut self) -> Result<Expr, CalcError> {
        let mut left = self.parse_term()?;
        loop {
            let (token, pos) = self.peek();
            let op = match token {
                Token::Plus => Op::Add,
                Token::Minus => Op::Sub,
                _ => return Ok(left),
            };
            self.next();
            let right = self.parse_term()?;
            // 지금까지 읽은 것이 통째로 새 마디의 왼쪽이 된다
            left = Expr::Bin(Box::new(left), op, pos, Box::new(right));
        }
    }

    // 항 = 인수 { ("*" | "/") 인수 }
    fn parse_term(&mut self) -> Result<Expr, CalcError> {
        let mut left = self.parse_factor()?;
        loop {
            let (token, pos) = self.peek();
            let op = match token {
                Token::Star => Op::Mul,
                Token::Slash => Op::Div,
                _ => return Ok(left),
            };
            self.next();
            let right = self.parse_factor()?;
            left = Expr::Bin(Box::new(left), op, pos, Box::new(right));
        }
    }

    // 인수 = 수 | "-" 인수 | "(" 식 ")"
    fn parse_factor(&mut self) -> Result<Expr, CalcError> {
        let (token, pos) = self.next();
        match token {
            Token::Num(n) => Ok(Expr::Num(n)),
            Token::Minus => {
                let inner = self.parse_factor()?;
                Ok(Expr::Neg(pos, Box::new(inner)))
            }
            Token::LParen => {
                let inner = self.parse_expr()?;
                // 괄호는 마디를 만들지 않는다. 짝만 확인한다
                match self.next() {
                    (Token::RParen, _) => Ok(inner),
                    _ => Err(CalcError::new(Kind::Unclosed, pos)),
                }
            }
            Token::End => Err(CalcError::new(Kind::Ended, pos)),
            _ => Err(CalcError::new(Kind::NotOperand, pos)),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::token::tokenize;

    // 줄을 토큰으로 나눠 곧바로 parse 에 넘긴다
    fn tree(line: &str) -> Result<Expr, CalcError> {
        parse(&tokenize(line)?)
    }

    // 나무를 {:?} 로 찍은 글. 읽지 못한 줄에서는 패닉한다
    fn show(line: &str) -> String {
        format!("{:?}", tree(line).unwrap())
    }

    fn err<T>(kind: Kind, pos: usize) -> Result<T, CalcError> {
        Err(CalcError::new(kind, pos))
    }

    #[test]
    fn minus_groups_to_the_left() {
        assert_eq!(tree("42"), Ok(Expr::Num(42)));
        let want = "Bin(Bin(Num(8), Sub, 2, Num(3)), Sub, 6, Num(2))";
        assert_eq!(show("8 - 3 - 2"), want);
        // 빈칸 없이 붙여 써도 같은 생김새다. 자리만 다르다
        let want = "Bin(Bin(Num(1), Add, 1, Num(2)), Sub, 3, Num(3))";
        assert_eq!(show("1+2-3"), want);
    }

    #[test]
    fn broken_lines_point_at_the_place() {
        assert_eq!(tree("1 +"), err(Kind::Ended, 3));
        assert_eq!(tree(""), err(Kind::Ended, 0));
        assert_eq!(tree("+ 1"), err(Kind::NotOperand, 0));
        assert_eq!(tree("1 + + 2"), err(Kind::NotOperand, 4));
        assert_eq!(tree("1 2"), err(Kind::Trailing, 2));
        // 토큰으로 나누다 난 오류는 ? 를 타고 그대로 나온다
        assert_eq!(tree("1 + 가"), err(Kind::UnknownChar, 4));
    }

    #[test]
    fn list_without_end_is_read_as_ended() {
        assert_eq!(parse(&[]), err(Kind::Ended, 0));
        assert_eq!(parse(&[(Token::Num(1), 0)]), Ok(Expr::Num(1)));
        assert_eq!(
            parse(&[(Token::Num(1), 0), (Token::Plus, 2)]),
            err(Kind::Ended, 0)
        );
    }

    #[test]
    fn times_binds_tighter_than_plus() {
        let want = "Bin(Num(2), Add, 2, Bin(Num(3), Mul, 6, Num(4)))";
        assert_eq!(show("2 + 3 * 4"), want);
        let want = "Bin(Bin(Num(2), Mul, 2, Num(3)), Add, 6, Num(4))";
        assert_eq!(show("2 * 3 + 4"), want);
        // 나눗셈도 왼쪽부터 묶인다
        let want = "Bin(Bin(Num(8), Div, 2, Num(4)), Div, 6, Num(2))";
        assert_eq!(show("8 / 4 / 2"), want);
        assert_eq!(tree("2 * * 3"), err(Kind::NotOperand, 4));
    }

    #[test]
    fn parentheses_leave_no_node() {
        let want = "Bin(Bin(Num(2), Add, 3, Num(3)), Mul, 8, Num(4))";
        assert_eq!(show("(2 + 3) * 4"), want);
        assert_eq!(show("((7))"), "Num(7)");
        assert_eq!(
            show("8 - (3 - 2)"),
            "Bin(Num(8), Sub, 2, Bin(Num(3), Sub, 7, Num(2)))"
        );
    }

    #[test]
    fn minus_in_front_is_a_sign() {
        assert_eq!(show("-3"), "Neg(0, Num(3))");
        assert_eq!(show("--3"), "Neg(0, Neg(1, Num(3)))");
        assert_eq!(
            show("2 - -3"),
            "Bin(Num(2), Sub, 2, Neg(4, Num(3)))"
        );
        // 부호는 곱셈보다 먼저 묶인다
        assert_eq!(
            show("-2 * 3"),
            "Bin(Neg(0, Num(2)), Mul, 3, Num(3))"
        );
        assert_eq!(
            show("-(2 * 3)"),
            "Neg(0, Bin(Num(2), Mul, 4, Num(3)))"
        );
        // 더하기 부호는 없다
        assert_eq!(tree("+3"), err(Kind::NotOperand, 0));
        assert_eq!(tree("-"), err(Kind::Ended, 1));
    }

    #[test]
    fn unbalanced_parentheses() {
        // 닫히지 않은 괄호는 여는 괄호의 자리를 알린다
        assert_eq!(tree("(1"), err(Kind::Unclosed, 0));
        assert_eq!(tree("(1 2"), err(Kind::Unclosed, 0));
        assert_eq!(tree("1 + ((2)"), err(Kind::Unclosed, 4));
        assert_eq!(tree("("), err(Kind::Ended, 1));
        assert_eq!(tree("()"), err(Kind::NotOperand, 1));
        assert_eq!(tree(")"), err(Kind::NotOperand, 0));
        assert_eq!(tree("1)"), err(Kind::Trailing, 1));
        // 괄호를 붙여 쓴다고 곱셈이 되지는 않는다
        assert_eq!(tree("2(3)"), err(Kind::Trailing, 1));
    }

    // 나무의 깊이 — 수 하나가 1 이다
    fn depth(expr: &Expr) -> usize {
        match expr {
            Expr::Num(_) => 1,
            Expr::Neg(_, inner) => 1 + depth(inner),
            Expr::Bin(left, _, _, right) => {
                1 + depth(left).max(depth(right))
            }
        }
    }

    #[test]
    fn two_hundred_tokens_are_read() {
        // 부호 199 개와 수 하나 — 토큰 200 개, 깊이도 200
        let line = "-".repeat(199) + "1";
        assert_eq!(tree(&line).map(|e| depth(&e)), Ok(200));
        // 괄호 99 겹 — 토큰 199 개. 괄호는 깊이를 더하지 않는다
        let line = "(".repeat(99) + "1" + &")".repeat(99);
        assert_eq!(tree(&line).map(|e| depth(&e)), Ok(1));
        // 1 을 백 번 더한다 — 토큰 199 개, 왼쪽으로 깊이 100
        let line = "1".to_string() + &"+1".repeat(99);
        assert_eq!(tree(&line).map(|e| depth(&e)), Ok(100));
    }

    #[test]
    fn token_201_is_refused() {
        // 자리는 201 번째 토큰이 있는 곳이다
        let line = "-".repeat(200) + "1";
        assert_eq!(tree(&line), err(Kind::TooLong, 200));
        let line = "(".repeat(100) + "1" + &")".repeat(100);
        assert_eq!(tree(&line), err(Kind::TooLong, 200));
        let line = "1".to_string() + &"+1".repeat(100);
        assert_eq!(tree(&line), err(Kind::TooLong, 200));
        // 한계를 넘는 줄은 다른 잘못이 있어도 TooLong 이다
        let line = "+".repeat(201);
        assert_eq!(tree(&line), err(Kind::TooLong, 200));
    }
}
