use std::slice;

// 첫 칸과 마지막 칸을 뺀 가운데를 슬라이스로 준다.
fn middle(xs: &[u32]) -> &[u32] {
    if xs.len() < 2 {
        return &[];
    }
    let p = xs.as_ptr();
    // 안전: 길이가 2 이상이므로 1번 칸부터 len - 2 칸은 모두 xs 안이다.
    // 그 칸들에는 값이 들어 있고, 돌려주는 슬라이스는 xs 를 빌린
    // 동안만 산다. 불변 참조라서 그동안 아무도 고치지 못한다.
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
