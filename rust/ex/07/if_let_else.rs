enum Token {
    Number(i64),
    Word(String),
    End,
}

fn show(t: &Token) {
    if let Token::Number(n) = t {
        println!("수 {n}");
    } else if let Token::Word(w) = t {
        println!("낱말 {w}");
    } else {
        println!("그 밖");
    }
}

fn main() {
    show(&Token::Number(42));
    show(&Token::Word(String::from("rust")));
    show(&Token::End);
}
