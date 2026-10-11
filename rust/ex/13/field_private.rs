mod bank {
    pub struct Account {
        pub owner: String,
        balance: u64, // pub 이 없다
    }

    pub fn open(owner: &str) -> Account {
        Account {
            owner: owner.to_string(),
            balance: 100,
        }
    }
}

fn main() {
    let a = bank::open("kim");
    println!("{}", a.owner); // 공개 필드는 읽을 수 있다
    println!("{}", a.balance);
}
//@ expect: E0616
