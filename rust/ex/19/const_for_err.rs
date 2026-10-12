// 0 부터 N-1 까지의 제곱을 컴파일할 때 채우려 한다.
const fn squares<const N: usize>() -> [u32; N] {
    let mut out = [0; N];
    for i in 0..N {
        out[i] = (i * i) as u32;
    }
    out
}

const TABLE: [u32; 6] = squares();

fn main() {
    println!("{TABLE:?}");
}
//@ expect: error
