use crate::error::{CalcError, Kind};
use crate::expr::{Expr, Op};
use crate::token::Token;

// 토큰 목록 전체를 식 하나로 읽는다
pub fn parse(tokens: &[(Token, usize)]) -> Result<Expr, CalcError> {
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

    // 식 = 인수 { ("+" | "-") 인수 }
    fn parse_expr(&mut self) -> Result<Expr, CalcError> {
        let mut left = self.parse_factor()?;
        loop {
            let (token, pos) = self.peek();
            let op = match token {
                Token::Plus => Op::Add,
                Token::Minus => Op::Sub,
                _ => return Ok(left),
            };
            self.next();
            let right = self.parse_factor()?;
            // 지금까지 읽은 것이 통째로 새 마디의 왼쪽이 된다
            left = Expr::Bin(Box::new(left), op, pos, Box::new(right));
        }
    }

    // 인수 = 수
    fn parse_factor(&mut self) -> Result<Expr, CalcError> {
        let (token, pos) = self.next();
        match token {
            Token::Num(n) => Ok(Expr::Num(n)),
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
}
