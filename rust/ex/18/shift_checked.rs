use std::env;

fn main() {
    // 미는 칸 수를 실행할 때 받는다
    let arg = env::args().nth(1).expect("칸 수가 없다");
    let n: u32 = arg.parse().expect("수가 아니다");
    let one: u8 = 1;
    // checked_shl 은 칸 수가 비트 수 이상이면 None 이다
    println!("checked_shl(7) {:?}", one.checked_shl(7));
    println!("checked_shl({n}) {:?}", one.checked_shl(n));
    // << 는 같은 경우에 패닉한다
    println!("1 << {n} = {}", one << n);
}
//@ args: 8
//@ exit: 101
