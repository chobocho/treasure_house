// url 칸의 상태 둘 — 비었다, 채웠다
struct NoUrl;
struct HasUrl(String);

struct Builder<U> {
    url: U,
    retries: u32,
}

impl Builder<NoUrl> {
    fn new() -> Builder<NoUrl> {
        let (url, retries) = (NoUrl, 0);
        Builder { url, retries }
    }

    // url 을 채우면 타입이 Builder<HasUrl> 로 바뀐다.
    fn url(self, url: &str) -> Builder<HasUrl> {
        let url = HasUrl(url.to_string());
        let retries = self.retries;
        Builder { url, retries }
    }
}

// 없어도 되는 칸은 어느 상태에서든 채운다.
impl<U> Builder<U> {
    fn retries(mut self, n: u32) -> Builder<U> {
        self.retries = n;
        self
    }
}

// build 는 url 을 채운 쪽에만 있고, 실패하지 않는다.
impl Builder<HasUrl> {
    fn build(self) -> String {
        let HasUrl(url) = self.url;
        format!("GET {url} (재시도 {})", self.retries)
    }
}

fn main() {
    // url 을 빠뜨렸다.
    let bad = Builder::new().retries(3).build();
    println!("{bad}");
}
//@ expect: E0599
