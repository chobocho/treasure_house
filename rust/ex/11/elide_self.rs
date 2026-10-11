struct Article {
    title: String,
    body: String,
}

impl Article {
    // &self 가 있으면, 나가는 참조의 수명은 self 의 것이다.
    fn headline(&self, prefix: &str) -> &str {
        println!("{prefix}");
        &self.title
    }
}

fn main() {
    let a = Article {
        title: String::from("Rust 2024"),
        body: String::from("..."),
    };
    let h = a.headline("[속보]");
    println!("{h} ({} 바이트 본문)", a.body.len());
}
