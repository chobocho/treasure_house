fn main() {
    let v: Vec<u32> = (1..=10).collect();

    let middle: Vec<&u32> = v.iter().skip(2).take(3).collect();
    let every3: Vec<&u32> = v.iter().step_by(3).collect();
    let backward: Vec<&u32> = v.iter().rev().take(2).collect();
    let joined: Vec<u32> = (1..=2).chain(8..=9).collect();

    println!("{middle:?}\n{every3:?}\n{backward:?}\n{joined:?}");
}
