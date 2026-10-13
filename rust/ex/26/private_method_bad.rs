mod bank {
    pub struct Account {
        pub balance: u32,
    }

    impl Account {
        fn audit(&self) -> u32 {
            self.balance
        }
    }
}

fn main() {
    let a = bank::Account { balance: 100 };
    println!("{}", a.audit());
}
//@ expect: E0624
