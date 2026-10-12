trait Lending {
    type Item<'a>
    where
        Self: 'a;

    fn next(&mut self) -> Option<Self::Item<'_>>;
}

struct Shouter {
    words: Vec<&'static str>,
    pos: usize,
    buf: String,
}

impl Lending for Shouter {
    type Item<'a> = &'a str;

    fn next(&mut self) -> Option<&str> {
        let word = self.words.get(self.pos)?;
        self.pos += 1;
        self.buf.clear();
        self.buf.push_str(word);
        self.buf.make_ascii_uppercase();
        Some(&self.buf)
    }
}

fn main() {
    // 표준 Iterator — 내준 둘을 함께 쥐고 있어도 된다.
    let mut plain = vec!["ab", "cd"].into_iter();
    let first = plain.next();
    let second = plain.next();
    println!("{first:?} {second:?}");

    // 빌려주는 쪽 — 다음을 부르기 전에 새 String 으로 옮겨 둔다.
    let words = vec!["ab", "cd"];
    let mut it = Shouter {
        words,
        pos: 0,
        buf: String::new(),
    };
    let first = it.next().map(String::from);
    let second = it.next().map(String::from);
    println!("{first:?} {second:?}");
}
