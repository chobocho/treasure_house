use std::collections::HashMap;

fn main() {
    let mut stock = HashMap::new();
    stock.insert("사과", 3);
    stock.insert("배", 5);

    // get 은 Option<&V> 를 준다 — 없는 키일 수 있으니까.
    println!("{:?} {:?}", stock.get("사과"), stock.get("감"));
    println!("{}", stock.get("감").copied().unwrap_or(0));
    println!("{} {}", stock.contains_key("배"), stock.len());
    println!("{:?} {:?}", stock.remove("배"), stock.remove("배"));
}
