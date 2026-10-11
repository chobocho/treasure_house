fn main() {
    let a = 5;
    let r = &a;
    // * 는 참조를 따라가 값을 읽는다
    let b = *r + 1;
    println!("{a} {b}");

    // 견줄 때는 양쪽을 맞춘다. 값끼리, 또는 참조끼리.
    println!("{} {}", *r == 5, r == &5);

    let mut n = 10;
    let m = &mut n;
    // &mut 를 따라가면 값을 고칠 수 있다
    *m += 1;
    *m *= 2;
    println!("{n}");
}
