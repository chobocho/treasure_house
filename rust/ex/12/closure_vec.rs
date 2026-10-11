fn main() {
    let bonus = 10;
    // 클로저는 저마다 타입이 다르다.
    // 한 벡터에 담으려면 Box<dyn Fn> 으로 만든다.
    let steps: Vec<Box<dyn Fn(i32) -> i32>> = vec![
        Box::new(|x| x + 1),
        Box::new(|x| x * 2),
        Box::new(move |x| x + bonus),
    ];

    let mut value = 5;
    for step in &steps {
        value = step(value);
    }
    println!("{value}");
}
