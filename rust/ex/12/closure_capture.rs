fn main() {
    let rate = 1.1;
    // 함수와 달리, 주변의 변수(rate)를 그대로 쓸 수 있다.
    let with_tax = |price: f64| price * rate;

    println!("{:.1}", with_tax(1000.0));
    println!("{:.1}", with_tax(250.0));
}
