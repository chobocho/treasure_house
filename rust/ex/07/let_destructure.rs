struct Point {
    x: i32,
    y: i32,
}

fn main() {
    // let 의 왼쪽은 패턴이다.
    let (a, b) = (1, "둘");
    let [first, second, _] = [10, 20, 30];
    let Point { x, y } = Point { x: 3, y: 4 };
    let ((p, q), r) = ((1, 2), 3);

    println!("{a} {b} {first} {second} {x} {y} {p} {q} {r}");

    let (mut lo, mut hi) = (1, 9);
    (lo, hi) = (hi, lo); // 대입에서도 풀어 헤친다 — 맞바꾸기
    lo += 1;
    hi -= 1;
    println!("{lo} {hi}");
}
