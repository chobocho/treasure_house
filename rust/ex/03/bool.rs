use std::any::type_name_of_val;

fn main() {
    // 견주는 식의 값이 bool 이다
    let passed = 82 >= 60;
    let absent = false;
    println!("passed = {passed} ({})", type_name_of_val(&passed));
    // ! 는 참과 거짓을 뒤집는다
    println!("!passed = {}, !absent = {}", !passed, !absent);
    // 수로 바꾸면 true 는 1, false 는 0 이다
    println!("{} {}", passed as i32, absent as i32);
    // 그래서 맞은 것의 개수를 더해서 셀 수 있다
    let hits = (3 + 4 == 7) as i32 + (2 * 2 == 5) as i32;
    println!("맞은 식 {hits}개");
    println!("bool 은 {}바이트", size_of::<bool>());
}
