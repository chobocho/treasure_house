use std::collections::HashMap;

fn main() {
    let stock = HashMap::from([("사과", 3), ("배", 5)]);
    println!("{}", stock["사과"]);
    println!("{}", stock["감"]); // 없는 키를 [] 로 읽으면 패닉한다
}
//@ exit: 101
