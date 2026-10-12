struct Buf<const N: usize = 16> {
    data: [u8; N],
}

impl<const N: usize> Buf<N> {
    fn new() -> Buf<N> {
        Buf { data: [0; N] }
    }
}

fn main() {
    // 타입을 어디에도 적지 않았다.
    let buf = Buf::new();
    println!("{}", buf.data.len());
}
//@ expect: error
