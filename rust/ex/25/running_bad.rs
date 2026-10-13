fn main() {
    let prices = [1200, 450, 3000, 80];
    let mut total = 0;
    // 값 하나를 합계에 보탠다.
    let mut add = |won: u32| total += won;

    for price in prices {
        add(price);
        println!("{price:>5} 까지 {total:>5}");
    }
    println!("모두 {total}원");
}
//@ expect: E0502
