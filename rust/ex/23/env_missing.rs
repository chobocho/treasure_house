fn main() {
    println!("{}", env!("GREETING"));
    println!("{}", env!("GREETING", "GREETING 을 정하고 빌드할 것"));
}
//@ expect: error
