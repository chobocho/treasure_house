struct Article {
    title: String,
}

impl Article {
    // self 와 prefix 를 같은 'a 로 묶는다 — 어느 쪽이든 돌려줄 수 있다.
    fn pick<'a>(&'a self, prefix: &'a str) -> &'a str {
        if self.title.is_empty() {
            prefix
        } else {
            &self.title
        }
    }
}

fn main() {
    let a = Article {
        title: String::new(),
    };
    println!("{}", a.pick("제목 없음"));
}
