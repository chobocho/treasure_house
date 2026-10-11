use std::collections::HashMap;

fn main() {
    let mut ages: HashMap<String, u32> = HashMap::new();
    ages.insert(String::from("kim"), 31);

    // 키가 String 이어도 찾을 때는 &str 로 된다.
    println!("{:?}", ages.get("kim"));
    // 값을 제자리에서 고친다.
    if let Some(age) = ages.get_mut("kim") {
        *age += 1;
    }
    ages.entry(String::from("kim")).and_modify(|a| *a += 10);
    println!("{:?}", ages.get("kim"));
}
