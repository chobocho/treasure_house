fn main() {
    // 함수 안에 함수를 둘 수 있다. 이 안에서만 보인다.
    fn square(x: i32) -> i32 {
        x * x
    }
    println!("{}", square(7));
}
