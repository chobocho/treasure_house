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

// 어떤 수명으로 빌려주든 그 Item 은 Display 여야 한다.
fn print_all<L>(mut it: L)
where
    L: Lending,
    for<'a> L::Item<'a>: std::fmt::Display,
{
    while let Some(x) = it.next() {
        println!("{x}");
    }
}

fn main() {
    let words = vec!["ab", "cd"];
    let (pos, buf) = (0, String::new());
    print_all(Shouter { words, pos, buf });
}
