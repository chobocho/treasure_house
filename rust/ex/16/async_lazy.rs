async fn fetch() -> u32 {
    println!("fetch 가 돈다");
    42
}

fn main() {
    fetch(); // 부르기만 하면 아무 일도 일어나지 않는다
    println!("끝");
}
//@ warnings: show
