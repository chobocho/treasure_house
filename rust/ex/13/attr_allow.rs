// 속성으로 특정 경고를 끈다 — 범위는 바로 아래 항목.
#[allow(dead_code)]
fn not_used_yet() {}

#[allow(unused_variables)]
fn main() {
    let spare = 1;
    println!("경고 없이 컴파일된다");
}
