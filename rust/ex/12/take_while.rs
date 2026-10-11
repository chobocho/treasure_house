fn main() {
    let v = [1, 3, 5, 6, 7, 9];

    // 조건이 처음 깨지는 곳에서 끝낸다 / 거기서부터 시작한다.
    let head: Vec<&i32> =
        v.iter().take_while(|x| **x % 2 == 1).collect();
    let tail: Vec<&i32> =
        v.iter().skip_while(|x| **x % 2 == 1).collect();
    println!("{head:?}\n{tail:?}");
}
