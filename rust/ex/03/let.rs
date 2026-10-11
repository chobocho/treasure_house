use std::any::type_name_of_val;

fn main() {
    // 타입을 적지 않으면 컴파일러가 값에서 추론한다
    let apples = 5;
    let price = 1200.5;
    // 이름 뒤에 : 타입 을 적어 직접 정할 수도 있다
    let count: i64 = 5;

    println!("apples = {apples} ({})", type_name_of_val(&apples));
    println!("price  = {price} ({})", type_name_of_val(&price));
    println!("count  = {count} ({})", type_name_of_val(&count));
}
