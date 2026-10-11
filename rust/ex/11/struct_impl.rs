struct Excerpt<'a> {
    part: &'a str,
}

// impl 뒤에도, 타입 이름 뒤에도 <'a> 를 적는다.
impl<'a> Excerpt<'a> {
    fn len(&self) -> usize {
        self.part.len()
    }

    // 결과를 self 가 아니라 원래 글('a)에 맨다.
    fn text(&self) -> &'a str {
        self.part
    }
}

fn main() {
    let novel = String::from("옛날 옛적에");
    let text;
    {
        let e = Excerpt { part: &novel };
        println!("{}", e.len());
        text = e.text();
    } // e 는 사라져도 novel 은 살아 있다
    println!("{text}");
}
