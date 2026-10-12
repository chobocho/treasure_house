// 가로와 세로가 둘 다 있어야 넓이가 나온다
fn area(width: Option<u32>, height: Option<u32>) -> Option<u32> {
    width.zip(height).map(|(w, h)| w * h)
}

// 쿠폰 할인과 회원 할인은 함께 쓸 수 없다. 하나만 있을 때 그 값
fn discount(coupon: Option<u32>, member: Option<u32>) -> Option<u32> {
    coupon.xor(member)
}

fn main() {
    // zip — 둘 다 Some 일 때만 짝이 된다
    println!("{:?}", Some(3).zip(Some('a')));
    println!("{:?}", Some(3).zip(None::<char>));
    println!("{:?} {:?}", area(Some(3), Some(4)), area(Some(3), None));

    // xor — 한쪽만 Some 일 때 그것을 준다
    println!("{:?}", discount(Some(3000), None));
    println!("{:?}", discount(None, Some(1000)));
    println!("{:?}", discount(Some(3000), Some(1000)));
    println!("{:?}", discount(None, None));

    // or 는 둘 다 있으면 앞의 것을 준다
    println!("{:?}", Some(3000).or(Some(1000)));
}
