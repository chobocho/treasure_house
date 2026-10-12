// T 의 기본값으로 채운 배열을 컴파일할 때 만들려 한다.
const fn filled<T: Default + Copy, const N: usize>() -> [T; N] {
    [T::default(); N]
}

const ZEROS: [u8; 4] = filled();

fn main() {
    println!("{ZEROS:?}");
}
//@ expect: E0015
