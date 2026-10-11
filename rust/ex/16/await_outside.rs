async fn fetch() -> u32 {
    42
}

fn main() {
    let n = fetch().await;
    println!("{n}");
}
//@ expect: E0728
