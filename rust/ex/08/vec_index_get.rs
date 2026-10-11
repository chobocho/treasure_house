fn main() {
    let v = vec![10, 20, 30];
    let i = v.len() + 4;

    // get 은 Option 을 준다 — 범위 밖이면 None.
    println!("{:?} {:?}", v.get(1), v.get(i));
    println!("{:?} {:?}", v.first(), v.last());
    // [] 는 범위 밖이면 패닉한다.
    println!("{}", v[1]);
    println!("{}", v[i]);
}
//@ exit: 101
