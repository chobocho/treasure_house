use std::array;

// 칸마다 클로저를 불러 채운다. 클로저는 칸의 번호를 받는다.
fn blank<T: Default, const N: usize>() -> [T; N] {
    array::from_fn(|_| T::default())
}

fn main() {
    let names: [String; 3] = blank();
    println!("{names:?}");
    let big: [u8; 40] = blank();
    println!("{}", big.len());
    // 번호를 쓰면 칸마다 다른 값이 된다.
    let squares: [usize; 5] = array::from_fn(|i| i * i);
    println!("{squares:?}");
    let labels: [String; 3] = array::from_fn(|i| format!("칸{i}"));
    println!("{labels:?}");
}
