use std::collections::BTreeSet;

fn main() {
    // 비어 있는 사물함 번호
    let mut free = BTreeSet::from([14, 3, 27, 8, 21]);
    println!("{free:?}");
    // 10 번 이상 가운데 가장 작은 번호
    println!("{:?}", free.range(10..).next());
    // 10 번보다 작은 것 가운데 가장 큰 번호
    println!("{:?}", free.range(..10).next_back());
    // 20 번대는 몇 개인가
    println!("{}", free.range(20..30).count());
    // 30 번 이상은 없다
    println!("{:?}", free.range(30..).next());

    // 가장 작은 번호와 가장 큰 번호
    println!("{:?} {:?}", free.first(), free.last());
    // 가장 작은 번호를 꺼내 내준다
    println!("{:?}", free.pop_first());
    println!("{free:?}");
}
