fn main() {
    let arr = [10, 20, 30, 40, 50];
    let v = vec![1, 2, 3];

    // 배열의 가운데 세 칸
    let mid: &[i32] = &arr[1..4];
    println!("{mid:?} len {} 첫 칸 {}", mid.len(), mid[0]);

    // 벡터의 1번 칸부터 끝까지
    let tail: &[i32] = &v[1..];
    println!("{tail:?} len {}", tail.len());

    // 전체를 가리키는 슬라이스
    let all = &arr[..];
    println!("{all:?} len {}", all.len());
}
