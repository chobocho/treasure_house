// 권한 하나에 비트 하나
const READ: u8 = 0b001;
const WRITE: u8 = 0b010;
const EXEC: u8 = 0b100;

fn show(perm: u8, what: &str) {
    let r = perm & READ != 0;
    let w = perm & WRITE != 0;
    let x = perm & EXEC != 0;
    println!(
        "{perm:03b}  읽기 {r:<5} 쓰기 {w:<5} 실행 {x:<5} ← {what}"
    );
}

fn main() {
    let mut perm = READ;
    show(perm, "처음");
    // 켜기 — | 로 그 비트를 보탠다
    perm |= WRITE | EXEC;
    show(perm, "쓰기와 실행을 켠다");
    // 끄기 — 그 비트만 0 인 값과 & 한다
    perm &= !WRITE;
    show(perm, "쓰기를 끈다");
    // 뒤집기 — ^ 는 켜진 비트를 끄고 꺼진 비트를 켠다
    perm ^= EXEC;
    show(perm, "실행을 뒤집는다");
    perm ^= EXEC;
    show(perm, "한 번 더 뒤집는다");
}
