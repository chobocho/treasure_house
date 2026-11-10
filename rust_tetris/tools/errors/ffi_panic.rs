// extern "C" 밖으로 패닉이 나가려 하면 되감지 않고 프로세스를 끝낸다.
extern "C" fn tt_init(cell: u32) -> u32 {
    if cell < 8 {
        panic!("cell 이 너무 작다: {cell}");
    }
    1
}

fn main() {
    let r = std::panic::catch_unwind(|| tt_init(4));
    println!("여기까지 오지 못한다: {r:?}");
}
