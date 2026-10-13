mod bank {
    pub struct Account {
        pub balance: u32,
    }

    impl Account {
        pub fn audit(&self) -> u32 {
            self.balance
        }
    }
}

fn main() {
    let a = bank::Account { balance: 100 };
    println!("{}", a.audit());
}
