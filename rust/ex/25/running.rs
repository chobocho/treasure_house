fn main() {
    let prices = [1200, 450, 3000, 80];
    let mut total = 0;
    // 값 하나를 합계에 보탠다.
    let mut add = |won: u32| {
        total += won;
        total
    };

    for price in prices {
        let so_far = add(price);
        println!("{price:>5} 까지 {so_far:>5}");
    }
    println!("모두 {total}원");
}
