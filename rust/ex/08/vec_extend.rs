fn main() {
    let mut a = vec![1, 2];
    let mut b = vec![3, 4];

    a.extend([10, 20]); // 반복자의 원소를 덧붙인다
    a.extend(&b); // 빌려서 복사해 넣는다
    println!("{a:?} {b:?}");
    a.append(&mut b); // b 의 것을 옮겨 온다 — b 는 빈다
    println!("{a:?} {b:?}");

    let joined = [vec![1], vec![2, 3]].concat();
    println!("{joined:?}");
}
