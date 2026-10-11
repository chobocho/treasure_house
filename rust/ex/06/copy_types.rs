fn main() {
    let a = 5;
    let mut b = a; // 정수는 값이 통째로 복사된다
    b += 1;
    println!("{a} {b}");

    let x = 2.5;
    let y = x;
    let t = true;
    let u = t;
    let c = 'r';
    let d = c;
    println!("{x} {y} {t} {u} {c} {d}");

    // Copy 타입만 담은 튜플과 배열도 Copy 다
    let p = (1, 2.0);
    let q = p;
    let arr = [1, 2, 3];
    let arr2 = arr;
    println!("{p:?} {q:?} {arr:?} {arr2:?}");
}
