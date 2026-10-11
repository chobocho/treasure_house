struct Article {
    title: String,
}

impl Article {
    // 규칙대로면 결과는 self 에 매인다. 그런데 prefix 를 돌려준다.
    fn pick(&self, prefix: &str) -> &str {
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
//@ expect: error
