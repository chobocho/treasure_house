use std::collections::HashMap;

fn main() {
    let mut stock = HashMap::from([("사과", 3)]);

    // entry — "이 키의 자리". 없으면 넣고, 그 값의 가변 참조를 준다.
    *stock.entry("사과").or_insert(0) += 1;
    *stock.entry("배").or_insert(0) += 1;
    stock.entry("감").or_insert(100); // 없을 때만 넣는다
    stock.entry("감").or_insert(999);

    println!("{} {} {}", stock["사과"], stock["배"], stock["감"]);
}
