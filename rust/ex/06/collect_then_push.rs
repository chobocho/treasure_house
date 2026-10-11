fn main() {
    let mut v = vec![1, 2, 3];

    // 도는 동안에는 넣을 것을 다른 벡터에 모아 둔다
    let mut extra = Vec::new();
    for x in &v {
        if *x == 2 {
            extra.push(20);
        }
    }
    // 다 돈 뒤에 넣는다. v 를 빌린 것이 아무것도 없다.
    for e in extra {
        v.push(e);
    }

    // 칸의 값만 필요하면 참조 대신 값을 복사해 둔다
    let first = v[0];
    v.push(4);
    println!("{first} {v:?}");
}
