fn total<I: Iterator<Item = u32>>(items: I) -> u32 {
    let mut sum = 0;
    for x in items {
        sum += x;
    }
    sum
}

fn main() {
    let v: Vec<u32> = vec![10, 20, 30];
    // iter() 는 u32 가 아니라 &u32 를 내준다.
    println!("{}", total(v.iter()));
}
//@ expect: E0271
