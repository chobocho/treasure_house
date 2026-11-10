// 첫 원소를 빌려 둔 채로 벡터를 늘린다 — 재할당이 일어나면 댕글링.
fn main() {
    let mut rows = vec![0u8; 3];
    let first = &rows[0];
    rows.push(1);
    println!("{first}");
}
