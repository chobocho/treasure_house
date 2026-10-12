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

// 어떤 칸이든 그 폭만큼의 빈 배열을 만들려 한다.
fn blank<F: Field>() -> [u8; F::WIDTH] {
    [b'.'; F::WIDTH]
}

fn main() {
    // 타입을 짚어 적은 연관 상수는 배열의 길이가 된다.
    let code = [b'.'; Code::WIDTH];
    let row = [0u8; Code::WIDTH + Name::WIDTH];
    println!("{} {}", code.len(), row.len());
    // 타입 인자로 칸을 고른다.
    let name = blank::<Name>();
    println!("{}", name.len());
}
//@ expect: error
