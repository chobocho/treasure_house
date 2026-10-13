// 메뉴에서 name 의 값을 찾는다
fn price(menu: &[(&str, u32)], name: &str) -> Option<u32> {
    for (item, won) in menu {
        if *item == name {
            return Some(*won);
        }
    }
    None
}

// 주문한 것이 모두 메뉴에 있으면 값의 합, 하나라도 없으면 None
fn total(menu: &[(&str, u32)], order: &[&str]) -> Option<u32> {
    let mut sum = 0;
    for name in order {
        sum += price(menu, name)?;
    }
    Some(sum)
}

// 쿠폰이 있으면 그만큼 깎는다. 0원 아래로는 내려가지 않는다.
fn pay(sum: u32, coupon: Option<u32>) -> u32 {
    let off = coupon.unwrap_or(0);
    if off > sum { 0 } else { sum - off }
}

fn main() {
    let menu = [("김밥", 3500), ("라면", 4000), ("우동", 5500)];
    println!("{:?} {:?}", price(&menu, "라면"), price(&menu, "짜장"));
    let orders =
        [vec!["김밥", "우동"], vec!["김밥", "짜장", "우동"], vec![]];
    for order in &orders {
        let names = order.join(" + ");
        match total(&menu, order) {
            Some(sum) => println!("[{names}] {sum}원"),
            None => println!("[{names}] 메뉴에 없는 것이 있다"),
        }
    }
    println!("{} {}", pay(9000, Some(1000)), pay(9000, None));
    println!("{}", pay(3500, Some(5000)));
}
