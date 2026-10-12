// 한 칸 늘린 배열을 돌려주려 한다.
fn push<const N: usize>(a: [u8; N], last: u8) -> [u8; N + 1] {
    let mut out = [last; N + 1];
    out[..N].copy_from_slice(&a);
    out
}

fn main() {
    println!("{:?}", push([1, 2], 3));
}
//@ expect: error
