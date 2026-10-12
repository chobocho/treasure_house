fn main() {
    let x: u8 = 0b1001_0110;
    println!("x                {x:08b}");
    // 밀려난 비트는 버리고, 빈 자리는 0 으로 채운다
    println!("x << 2           {:08b}", x << 2);
    println!("x >> 2           {:08b}", x >> 2);
    // rotate 는 밀려난 비트를 반대쪽으로 돌려 넣는다
    println!("x.rotate_left(2) {:08b}", x.rotate_left(2));
    // 왼쪽 한 칸은 2 배, 오른쪽 한 칸은 2 로 나눈 몫
    println!("5 << 1 = {}, 20 >> 2 = {}", 5 << 1, 20 >> 2);

    // 부호 있는 타입의 >> 는 빈 자리를 부호 비트로 채운다
    let neg: i8 = -8;
    println!("neg              {neg:08b} = {neg}");
    println!("neg >> 1         {:08b} = {}", neg >> 1, neg >> 1);
    // 같은 비트를 u8 로 읽고 밀면 0 으로 채운다
    let raw = neg as u8;
    println!("raw >> 1         {:08b} = {}", raw >> 1, raw >> 1);
}
