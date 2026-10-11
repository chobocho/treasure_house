// 빌리는 대신 갖는다 — 수명 표기가 필요 없다.
struct Excerpt {
    part: String,
}

fn make() -> Excerpt {
    let novel = String::from("옛날 옛적에. 한 마을이 있었다.");
    let first = novel.split('.').next().unwrap_or("");
    Excerpt {
        part: first.to_string(), // 복사해서 가진다
    }
}

fn main() {
    let e = make(); // novel 은 이미 사라졌지만 괜찮다
    println!("{}", e.part);
}
