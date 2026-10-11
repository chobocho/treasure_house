struct Excerpt<'a> {
    part: &'a str,
}

impl<'a> Excerpt<'a> {
    // 'a 를 적지 않았다 — 생략 규칙이 결과를 self 에 맨다.
    fn text(&self) -> &str {
        self.part
    }
}

fn main() {
    let novel = String::from("옛날 옛적에");
    let text;
    {
        let e = Excerpt { part: &novel };
        text = e.text();
    } // e 가 사라진다 — novel 은 살아 있는데도 막힌다
    println!("{text}");
}
//@ expect: E0597
