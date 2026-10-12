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

// Item 에 아무 조건도 달지 않았다.
fn print_all<L: Lending>(mut it: L) {
    while let Some(x) = it.next() {
        println!("{x}");
    }
}

fn main() {
    let words = vec!["ab", "cd"];
    let (pos, buf) = (0, String::new());
    print_all(Shouter { words, pos, buf });
}
//@ expect: E0277
