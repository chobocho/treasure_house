// 아직 안 채운 칸을 Option 으로 들고 다닌다.
struct Builder {
    url: Option<String>,
    retries: u32,
}

impl Builder {
    fn new() -> Builder {
        let (url, retries) = (None, 0);
        Builder { url, retries }
    }

    fn url(mut self, url: &str) -> Builder {
        self.url = Some(url.to_string());
        self
    }

    fn retries(mut self, n: u32) -> Builder {
        self.retries = n;
        self
    }

    // url 을 채웠는지는 돌려 봐야 안다.
    fn build(self) -> Result<String, String> {
        let url = self.url.ok_or("url 이 없다")?;
        Ok(format!("GET {url} (재시도 {})", self.retries))
    }
}

fn main() {
    let ok = Builder::new().url("/health").retries(3).build();
    println!("{ok:?}");
    // url 을 빠뜨렸다.
    let bad = Builder::new().retries(3).build();
    println!("{bad:?}");
}
