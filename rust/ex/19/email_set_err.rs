mod mail {
    pub struct Email {
        addr: String,
    }

    impl Email {
        pub fn parse(text: &str) -> Result<Email, String> {
            if text.contains('@') {
                let addr = text.to_lowercase();
                Ok(Email { addr })
            } else {
                Err(format!("주소가 아님: {text}"))
            }
        }

        pub fn as_str(&self) -> &str {
            &self.addr
        }
    }
}

use mail::Email;

fn main() {
    let mut real = Email::parse("kim@example.com").unwrap();
    // 검사를 통과한 값의 속을 바꾸려 한다.
    real.addr = String::from("주소 아님");
    println!("{}", real.as_str());
}
//@ expect: E0616
