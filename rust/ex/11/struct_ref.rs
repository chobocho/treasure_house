// Excerpt 는 자기가 빌린 글보다 오래 살 수 없다.
struct Excerpt<'a> {
    part: &'a str,
}

fn main() {
    let novel = String::from("옛날 옛적에. 한 마을이 있었다.");
    let first = novel.split('.').next().unwrap_or("");
    let e = Excerpt { part: first };
    println!("{}", e.part);
}
