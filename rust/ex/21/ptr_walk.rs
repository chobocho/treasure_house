// 슬라이스의 합을 포인터 둘로 구한다.
fn sum(xs: &[u32]) -> u32 {
    let mut p = xs.as_ptr();
    // 안전: 길이만큼 나아간 곳은 마지막 칸 바로 다음이다. 거기까지는
    // 가리키는 포인터를 만들어도 된다. 따라가지는 않는다.
    let end = unsafe { p.add(xs.len()) };
    let mut total = 0;
    while p != end {
        // 안전: p 는 아직 end 가 아니므로 xs 의 칸 하나를 가리킨다.
        // 한 칸 나아간 곳은 다음 칸이거나 end 다.
        unsafe {
            total += *p;
            p = p.add(1);
        }
    }
    total
}

fn main() {
    let xs = [10, 20, 30, 40];
    // 반복자로 구한 합과 견준다.
    println!("{} {}", sum(&xs), xs.iter().sum::<u32>());
    println!("{}", sum(&[7]));
    println!("{}", sum(&[]));
}
