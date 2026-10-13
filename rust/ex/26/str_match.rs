fn price(size: &str) -> u32 {
    match size {
        "small" => 3000,
        "large" => 4500,
        _ => 0,
    }
}

fn main() {
    println!("{} {}", price("small"), price("large"));
    println!("{}", price("xl"));
}
