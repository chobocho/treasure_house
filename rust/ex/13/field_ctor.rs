mod bank {
    pub struct Account {
        pub owner: String,
        balance: u64,
    }

    impl Account {
        // 밖에서는 직접 만들 수 없으니 생성 함수를 내준다.
        pub fn new(owner: &str) -> Account {
            Account {
                owner: owner.to_string(),
                balance: 0,
            }
        }

        pub fn deposit(&mut self, amount: u64) {
            self.balance += amount;
        }

        pub fn balance(&self) -> u64 {
            self.balance
        }
    }
}

fn main() {
    let mut a = bank::Account::new("kim");
    a.deposit(100);
    println!("{} {}", a.owner, a.balance());
}
