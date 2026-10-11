// 수식 나무 — 재귀 타입의 흔한 쓰임새.
enum Expr {
    Num(f64),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
}

use Expr::{Add, Mul, Num};

fn eval(e: &Expr) -> f64 {
    match e {
        Num(n) => *n,
        Add(a, b) => eval(a) + eval(b),
        Mul(a, b) => eval(a) * eval(b),
    }
}

fn main() {
    // (1 + 2) * 4
    let e = Mul(
        Box::new(Add(Box::new(Num(1.0)), Box::new(Num(2.0)))),
        Box::new(Num(4.0)),
    );
    println!("{}", eval(&e));
}
