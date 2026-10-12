use std::slice;

// 첫 칸과 마지막 칸을 뺀 가운데를 슬라이스로 준다.
fn middle(xs: &[u32]) -> &[u32] {
    if xs.len() < 2 {
        return &[];
    }
    let p = xs.as_ptr();
    // 안전: p 는 슬라이스의 포인터라 널이 아니고 정렬이 맞다. 길이가 2
    // 이상이라 1번 칸부터 len - 2 칸은 xs 안이고 값이 들어 있다. 돌려준
    // 슬라이스는 xs 를 빌린 동안만 살아서 그동안 아무도 고치지 못한다.
    unsafe { slice::from_raw_parts(p.add(1), xs.len() - 2) }
}

fn main() {
    let xs = [10, 20, 30, 40, 50];
    let mid = middle(&xs);
    println!("{mid:?} {}", mid.len());
    // 안전한 길로 얻은 것과 같다.
    println!("{}", mid == &xs[1..4]);
    println!("{:?} {:?}", middle(&[1, 2]), middle(&[1]));
}
