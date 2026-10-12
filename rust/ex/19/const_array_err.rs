trait Field {
    const WIDTH: usize;
}

struct Code;

impl Field for Code {
    const WIDTH: usize = 4;
}

// 어떤 칸이든 그 폭만큼의 빈 배열을 만들려 한다.
fn blank<F: Field>() -> [u8; F::WIDTH] {
    [b'.'; F::WIDTH]
}

fn main() {
    println!("{}", blank::<Code>().len());
}
//@ expect: error
