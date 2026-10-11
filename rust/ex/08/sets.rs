use std::collections::BTreeSet;

fn main() {
    let mut seen = BTreeSet::new();
    // insert 는 "새로 들어갔는가" 를 bool 로 알려 준다.
    println!(
        "{} {} {}",
        seen.insert(3),
        seen.insert(1),
        seen.insert(3)
    );
    println!("{seen:?} {}", seen.contains(&1));

    let a: BTreeSet<u32> = [1, 2, 3, 4].into();
    let b: BTreeSet<u32> = [3, 4, 5].into();
    println!("{:?}", a.intersection(&b).collect::<Vec<_>>());
    println!("{:?}", a.union(&b).collect::<Vec<_>>());
    println!("{:?}", a.difference(&b).collect::<Vec<_>>());
}
