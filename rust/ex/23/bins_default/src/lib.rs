/// 인사말과 이름으로 한 줄을 만든다.
pub fn line(word: &str, name: &str) -> String {
    format!("{word}, {name}!")
}
