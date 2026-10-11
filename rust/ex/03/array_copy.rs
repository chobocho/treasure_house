fn main() {
    let a = [1, 2, 3];
    // 대입하면 모든 칸이 복사된다
    let mut b = a;
    println!("복사 직후 같은가? {}", a == b);
    b[0] = 99;
    // b 를 바꿔도 a 는 그대로이고, a 도 여전히 쓸 수 있다
    println!("a = {a:?}");
    println!("b = {b:?}");
    // 길이가 같은 두 배열은 칸마다 견준다
    println!("a == b ? {}", a == b);
    println!("a == [1, 2, 3] ? {}", a == [1, 2, 3]);
    println!("a != b ? {}", a != b);
}
