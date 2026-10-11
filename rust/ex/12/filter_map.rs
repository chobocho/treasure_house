fn main() {
    let inputs = ["10", "x", "30", ""];

    // filter_map — 바꾸면서 거른다. Some 만 남는다.
    let numbers: Vec<i32> =
        inputs.iter().filter_map(|s| s.parse().ok()).collect();
    println!("{numbers:?}");
}
