#[derive(Debug)]
struct Request {
    url: String,
    retries: u32,
    verbose: bool,
}

impl Request {
    fn new(url: &str) -> Self {
        Self {
            url: String::from(url),
            retries: 0,
            verbose: false,
        }
    }

    // self 를 받아 고친 뒤 다시 돌려준다 — 점으로 이어 쓸 수 있다.
    fn retries(mut self, n: u32) -> Self {
        self.retries = n;
        self
    }

    fn verbose(mut self) -> Self {
        self.verbose = true;
        self
    }
}

fn main() {
    let r = Request::new("example.com").retries(3).verbose();
    println!("{r:?}");
    println!("{} {} {}", r.url, r.retries, r.verbose);
}
