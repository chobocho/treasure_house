fn save(text: &str) -> Result<(), String> {
    if text.is_empty() {
        return Err(String::from("빈 글은 저장할 수 없다"));
    }
    Ok(())
}

fn main() {
    save(""); // 실패했는데 아무도 보지 않는다
    println!("저장 끝?");
}
//@ warnings: show
