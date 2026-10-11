fn main() {
    let mut total = 0;
    let mut add = |n: i32| total += n;

    add(10);
    println!("{total}"); // 클로저가 가변으로 빌린 동안 읽으려 한다
    add(5);
}
//@ expect: E0502
