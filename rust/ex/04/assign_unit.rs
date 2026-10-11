fn main() {
    let mut a = 1;
    println!("{a}");
    let b = a = 5; // 대입식의 값은 5 가 아니라 () 다
    println!("{a} {b:?}");
}
