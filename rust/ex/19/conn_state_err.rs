use std::marker::PhantomData;

// 상태 하나가 타입 하나다. 필드가 없어 크기는 0 이다.
struct Closed;
struct Open;

struct Conn<S> {
    host: String,
    state: PhantomData<S>,
}

impl Conn<Closed> {
    fn new(host: &str) -> Conn<Closed> {
        let host = host.to_string();
        let state = PhantomData;
        Conn { host, state }
    }

    // self 를 가져가고 다음 상태의 값을 돌려준다.
    fn open(self) -> Conn<Open> {
        let (host, state) = (self.host, PhantomData);
        Conn { host, state }
    }
}

// send 는 열린 연결에만 있다.
impl Conn<Open> {
    fn send(&self, msg: &str) {
        println!("{} 로 보냄: {msg}", self.host);
    }

    fn close(self) -> Conn<Closed> {
        let (host, state) = (self.host, PhantomData);
        Conn { host, state }
    }
}

fn main() {
    let conn = Conn::new("db");
    conn.send("hello");
    let conn = conn.close();
    conn.open().send("again");
    println!("{} {}", size_of::<Conn<Open>>(), size_of::<String>());
    println!("{}", size_of::<Open>());
}
//@ expect: E0599
