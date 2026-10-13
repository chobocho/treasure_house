fn main() {
    let mut stock = HashMap::new();
    stock.insert("사과", 3);
    println!("{:?}", stock.get("사과"));
}
//@ expect: E0433
