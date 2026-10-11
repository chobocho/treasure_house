mod bank {
    pub struct Account {
        pub owner: String,
        balance: u64, // pub 이 없다
    }

    impl Account {
        pub fn balance(&self) -> u64 {
            self.balance
        }
    }
}

fn main() {
    // 비공개 필드가 하나라도 있으면 밖에서 직접 만들 수 없다.
    let a = bank::Account {
        owner: String::from("kim"),
        balance: 100,
    };
    println!("{} {}", a.owner, a.balance());
}
//@ expect: E0451
