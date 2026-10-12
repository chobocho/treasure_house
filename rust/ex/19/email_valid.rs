mod mail {
    // 필드가 비공개라서 모듈 밖에서는 parse 로만 만든다.
    pub struct Email {
        addr: String,
    }

    impl Email {
        pub fn parse(text: &str) -> Result<Email, String> {
            match text.split_once('@') {
                Some((name, host))
                    if !name.is_empty() && host.contains('.') =>
                {
                    let addr = text.to_lowercase();
                    Ok(Email { addr })
                }
                _ => Err(format!("주소가 아님: {text}")),
            }
        }

        pub fn as_str(&self) -> &str {
            &self.addr
        }
    }
}

use mail::Email;

// Email 을 받는 함수는 다시 검사하지 않는다.
fn send(to: &Email) {
    println!("{} 에게 보냄", to.as_str());
}

fn main() {
    for text in ["Kim@Example.com", "kim.example.com", "@a.b"] {
        match Email::parse(text) {
            Ok(addr) => send(&addr),
            Err(e) => println!("{e}"),
        }
    }
}
