// N 을 적지 않으면 16 이다.
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
    let small = Buf::new();
    let big: Buf<64> = Buf::new();
    println!("{} {}", small.data.len(), big.data.len());
    println!("{}", size_of::<Buf>());
}
//@ expect: E0284
