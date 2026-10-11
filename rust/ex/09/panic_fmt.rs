fn withdraw(balance: u32, amount: u32) -> u32 {
    if amount > balance {
        panic!("출금 {amount} > 잔액 {balance}");
    }
    balance - amount
}

fn main() {
    println!("{}", withdraw(100, 30));
    println!("{}", withdraw(100, 300));
}
//@ exit: 101
