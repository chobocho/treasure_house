// 받은 구간의 칸을 모두 0 으로 만든다
fn zero(xs: &mut [i32]) {
    for x in xs {
        *x = 0;
    }
}

fn main() {
    let mut arr = [5, 3, 8, 1, 9, 2];

    // 앞의 네 칸만 정렬한다
    arr[..4].sort();
    println!("{arr:?}");

    // 뒤의 두 칸만 넘긴다
    zero(&mut arr[4..]);
    println!("{arr:?}");

    // 슬라이스의 0번은 배열의 1번이다
    let part = &mut arr[1..3];
    part[0] = 100;
    println!("{arr:?}");
}
