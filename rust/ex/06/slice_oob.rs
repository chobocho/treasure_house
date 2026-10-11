fn main() {
    let v = vec![10, 20, 30];
    println!("{:?}", &v[1..3]);

    // 끝이 길이를 넘는다
    println!("{:?}", &v[1..5]);
}
//@ exit: 101
