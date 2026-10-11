// FnOnce — 한 번만 부를 수 있는 클로저. 붙잡은 값을 써 버린다.
fn run(job: impl FnOnce() -> String) -> String {
    job()
}

fn main() {
    let name = String::from("ferris");
    // name 을 밖으로 내보낸다 — 두 번 할 수는 없는 일이다.
    let consume = move || name;
    println!("{}", run(consume));
}
