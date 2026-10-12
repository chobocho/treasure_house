// stats 기능을 켰을 때만 컴파일되는 함수.
#[cfg(feature = "stats")]
fn stats(words: &[&str]) -> String {
    format!("낱말 {}개", words.len())
}

fn main() {
    let words = ["red", "green", "blue"];
    println!("{}", words.join(" "));
    #[cfg(feature = "stats")]
    println!("{}", stats(&words));
}
