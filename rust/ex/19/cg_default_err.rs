// 기본값으로 채운 N 칸짜리 배열을 만들려 한다.
fn blank<T: Default, const N: usize>() -> [T; N] {
    Default::default()
}

fn main() {
    let names: [String; 3] = blank();
    println!("{names:?}");
}
//@ expect: E0277
