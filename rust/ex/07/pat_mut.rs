enum Account {
    Open { balance: u32 },
    Closed,
}

fn deposit(a: &mut Account, amount: u32) {
    // &mut 를 match 하면 꺼낸 것이 &mut 다 — 제자리에서 고친다.
    match a {
        Account::Open { balance } => *balance += amount,
        Account::Closed => println!("닫힌 계좌"),
    }
}

fn main() {
    let mut a = Account::Open { balance: 100 };
    deposit(&mut a, 50);
    match &a {
        Account::Open { balance } => println!("{balance}"),
        Account::Closed => {}
    }
    deposit(&mut Account::Closed, 1);
}
