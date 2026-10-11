fn withdraw(balance: u32, amount: u32) -> u32 {
    if amount > balance {
        panic!("잔액 {balance} 에서 {amount} 를 뺄 수 없다");
    }
    balance - amount
}

fn main() {
    println!("{}", withdraw(100, 30));
    println!("{}", withdraw(100, 300));
}
//@ exit: 101
