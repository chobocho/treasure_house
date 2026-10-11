#[must_use]
fn checksum(data: &[u8]) -> u32 {
    data.iter().map(|b| *b as u32).sum()
}

fn main() {
    checksum(b"rust"); // 계산만 하고 결과를 버렸다
    println!("끝");
}
//@ warnings: show
