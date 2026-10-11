fn main() {
    let count = 3;
    let name = "";
    // 조건은 bool 이어야 한다 — 무엇과 견주는지 직접 쓴다.
    if count != 0 {
        println!("있다");
    }
    if name.is_empty() {
        println!("이름이 비었다");
    }
}
