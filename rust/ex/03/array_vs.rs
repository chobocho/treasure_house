use std::any::type_name_of_val;

fn main() {
    // 배열 — 길이가 타입에 적혀 있다
    let array = [10, 20, 30];
    // 슬라이스 — 배열의 한 구간을 가리킨다
    let slice = &array[0..2];
    // Vec — 실행 중에 늘어난다
    let mut vector = vec![10, 20, 30];
    vector.push(40);
    println!("{array:?} {}", type_name_of_val(&array));
    println!("{slice:?} {}", type_name_of_val(&slice));
    println!("{vector:?} {}", type_name_of_val(&vector));
    println!("길이 {} {} {}", array.len(), slice.len(), vector.len());
}
