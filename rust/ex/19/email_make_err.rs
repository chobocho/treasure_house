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
    let real = Email::parse("kim@example.com").unwrap();
    // 검사를 거치지 않고 만들려 한다.
    let fake = Email {
        addr: String::from("주소 아님"),
    };
    println!("{} {}", real.as_str(), fake.as_str());
}
//@ expect: E0451
