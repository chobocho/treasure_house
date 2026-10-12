// 열렸는지를 bool 필드로 들고 다닌다.
struct Conn {
    host: String,
    open: bool,
}

impl Conn {
    fn new(host: &str) -> Conn {
        Conn {
            host: host.to_string(),
            open: false,
        }
    }

    fn open(&mut self) {
        self.open = true;
    }

    // 부를 때마다 상태를 확인해야 한다.
    fn send(&self, msg: &str) -> Result<(), String> {
        if !self.open {
            return Err(format!("{}: 열지 않은 연결", self.host));
        }
        println!("{} 로 보냄: {msg}", self.host);
        Ok(())
    }
}

fn main() {
    let mut conn = Conn::new("db");
    // open 을 부르는 것을 잊었다.
    if let Err(e) = conn.send("hello") {
        println!("{e}");
    }
    conn.open();
    if let Err(e) = conn.send("hello") {
        println!("{e}");
    }
}
