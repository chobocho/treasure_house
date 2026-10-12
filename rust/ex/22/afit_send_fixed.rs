trait Source {
    async fn fetch(&self) -> u32;
}

struct Fixed(u32);

impl Source for Fixed {
    async fn fetch(&self) -> u32 {
        self.0
    }
}

// Send 인 값만 받는다. 받아서 하는 일은 없다.
fn need_send<T: Send>(_: T) {}

// Fixed 만 받아, fetch 가 돌려준 퓨처를 need_send 에 넘긴다.
fn check(source: &Fixed) {
    need_send(source.fetch());
}

fn main() {
    check(&Fixed(1));
    println!("컴파일됐다");
}
