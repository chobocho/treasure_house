fn main() {
    let input = Some(5);
    if let Some(n) = input && n > 3 {
        println!("{n}");
    }
}
//@ edition: 2021
//@ expect: error
