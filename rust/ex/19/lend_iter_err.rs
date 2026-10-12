// 낱말을 하나씩 대문자로 바꿔 내준다. 버퍼 하나를 돌려 쓴다.
struct Shouter {
    words: Vec<&'static str>,
    pos: usize,
    buf: String,
}

impl Iterator for Shouter {
    type Item = &str;

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
    let words = vec!["ab", "cd"];
    let it = Shouter {
        words,
        pos: 0,
        buf: String::new(),
    };
    for w in it {
        println!("{w}");
    }
}
//@ expect: error
