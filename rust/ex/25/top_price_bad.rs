// 가장 큰 값이 든 칸을 가리키는 참조를 돌려준다
fn largest(prices: &[u32]) -> &u32 {
    let mut at = 0;
    for i in 1..prices.len() {
        if prices[i] > prices[at] {
            at = i;
        }
    }
    &prices[at]
}

fn main() {
    let mut prices = [300, 1200, 800];
    let before = largest(&prices);
    // 가장 비싼 것을 깎는다
    prices[1] = 700;
    let after = largest(&prices);
    println!("깎기 전 {before}원, 깎은 뒤 {after}원");
}
//@ expect: E0506
