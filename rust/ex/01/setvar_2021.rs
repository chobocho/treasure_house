fn main() {
    std::env::set_var("DECK", "rust");
    println!("{:?}", std::env::var("DECK"));
}
//@ edition: 2021
