// 빌려주는 반복자 — 내준 것은 다음 next 전까지만 쓸 수 있다.
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
        // 내 버퍼를 빌려준다.
        Some(&self.buf)
    }
}

fn main() {
    let words = vec!["ab", "cd", "ef"];
    let mut it = Shouter {
        words,
        pos: 0,
        buf: String::new(),
    };
    let first = it.next();
    let second = it.next();
    println!("{first:?} {second:?}");
}
//@ expect: E0499
