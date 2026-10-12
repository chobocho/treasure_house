struct Closed;
struct Open;

// 이 타입의 값을 받지 않고 버리면 경고하게 한다.
#[must_use = "open 이 돌려준 연결을 받아서 써야 한다"]
struct Conn<S> {
    host: &'static str,
    _state: S,
}

impl Conn<Closed> {
    fn new(host: &'static str) -> Conn<Closed> {
        let _state = Closed;
        Conn { host, _state }
    }

    fn open(self) -> Conn<Open> {
        let (host, _state) = (self.host, Open);
        Conn { host, _state }
    }
}

impl Conn<Open> {
    fn send(&self, msg: &str) {
        println!("{} 로 보냄: {msg}", self.host);
    }
}

fn main() {
    let conn = Conn::new("db");
    // 돌려준 Conn<Open> 을 받지 않았다.
    conn.open();
    let conn = Conn::new("db").open();
    conn.send("hello");
}
//@ warnings: show
