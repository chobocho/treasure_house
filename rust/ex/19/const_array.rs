trait Field {
    // 이 칸이 차지하는 바이트 수
    const WIDTH: usize;
}

struct Code;
struct Name;

impl Field for Code {
    const WIDTH: usize = 4;
}

impl Field for Name {
    const WIDTH: usize = 12;
}

// 길이를 const 제네릭 N 으로 받는다.
fn blank<const N: usize>() -> [u8; N] {
    [b'.'; N]
}

fn main() {
    // 타입을 짚어 적은 연관 상수는 배열의 길이가 된다.
    let code = [b'.'; Code::WIDTH];
    let row = [0u8; Code::WIDTH + Name::WIDTH];
    println!("{} {}", code.len(), row.len());
    // 부르는 쪽에서 타입을 짚어 N 으로 넘긴다.
    let name = blank::<{ Name::WIDTH }>();
    println!("{}", name.len());
}
