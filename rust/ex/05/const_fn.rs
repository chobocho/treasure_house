// const fn 은 컴파일하는 동안에도 부를 수 있다.
const fn kib(n: usize) -> usize {
    n * 1024
}

const BUFFER: usize = kib(4); // 컴파일 때 계산된다
static TABLE: [u8; kib(1)] = [0; kib(1)]; // 배열 길이 자리에도

fn main() {
    println!("{BUFFER} {}", TABLE.len());
    // 실행 중에 평소처럼 불러도 된다
    println!("{}", kib(std::env::args().count()));
}
