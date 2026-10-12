fn main() {
    let xs: [u32; 4] = [10, 20, 30, 40];
    // 첫 칸을 가리키는 날 포인터. 만드는 것은 안전하다.
    let p: *const u32 = xs.as_ptr();

    // 안전: xs 는 네 칸이고, 아래에서 가리키는 0·1·2 번 칸은 모두 그
    // 안이다. xs 는 이 블록 내내 살아 있고 그동안 아무도 고치지 않는다.
    unsafe {
        let third = p.add(2);
        println!("{} {}", *p, *third);
        // offset 은 부호가 있는 수를 받는다. 한 칸 앞으로.
        println!("{}", *third.offset(-1));
        // 같은 배열 안의 두 포인터 사이를 칸 수로 센다.
        println!("{}", third.offset_from(p));
        // 주소의 차이는 바이트로 센 값이다.
        println!("{}", third as usize - p as usize);
    }
}
