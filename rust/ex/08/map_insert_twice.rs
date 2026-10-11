use std::collections::HashMap;

fn main() {
    let mut stock = HashMap::new();
    // insert 는 그 키에 있던 옛 값을 돌려준다.
    println!("{:?}", stock.insert("사과", 3));
    println!("{:?}", stock.insert("사과", 10)); // 덮어쓴다
    println!("{:?}", stock.get("사과"));
}
