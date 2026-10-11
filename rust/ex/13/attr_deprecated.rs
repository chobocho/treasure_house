#[deprecated(note = "new_api 를 쓰세요")]
fn old_api() -> u32 {
    1
}

fn new_api() -> u32 {
    2
}

fn main() {
    println!("{} {}", old_api(), new_api());
}
//@ warnings: show
