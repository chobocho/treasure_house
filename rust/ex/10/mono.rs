use std::mem::size_of;

struct Wrapper<T> {
    value: T,
}

fn main() {
    // Wrapper<u8> 과 Wrapper<u64> 는 따로 컴파일되는 다른 타입이다.
    println!("{}", size_of::<Wrapper<u8>>());
    println!("{}", size_of::<Wrapper<u64>>());
    println!("{}", size_of::<Wrapper<[u8; 100]>>());
    let w = Wrapper { value: 7u16 };
    println!("{}", w.value);
}
