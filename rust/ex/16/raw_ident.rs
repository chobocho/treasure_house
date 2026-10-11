// 키워드와 같은 이름은 r# 를 붙여 쓴다.
fn r#match(text: &str, r#in: &str) -> bool {
    r#in.contains(text)
}

fn main() {
    let r#type = "rust";
    println!("{}", r#match(r#type, "trust"));
}
