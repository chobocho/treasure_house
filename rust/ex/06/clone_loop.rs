// 값을 받는다. 부르는 쪽은 벡터를 내놓아야 한다.
fn total_owned(v: Vec<i32>) -> i32 {
    let mut sum = 0;
    for x in v {
        sum += x;
    }
    sum
}

// 빌려 받는다. 부르는 쪽은 아무것도 잃지 않는다.
fn total(v: &[i32]) -> i32 {
    let mut sum = 0;
    for x in v {
        sum += x;
    }
    sum
}

fn main() {
    let v = vec![1, 2, 3];
    let mut a = 0;
    let mut b = 0;
    for _ in 0..3 {
        // 돌 때마다 벡터를 통째로 복사한다
        a += total_owned(v.clone());
        // 복사할 것이 없다
        b += total(&v);
    }
    println!("{a} {b}");
}
