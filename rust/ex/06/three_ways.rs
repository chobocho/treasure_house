// 보기만 한다 → & 로 빌린다
fn is_long(s: &str) -> bool {
    s.len() > 3
}

// 그 자리에서 고친다 → &mut 로 빌린다
fn add_mark(s: &mut String) {
    s.push('!');
}

// 넣어 두고 계속 가진다 → 값을 받는다
fn keep(list: &mut Vec<String>, s: String) {
    list.push(s);
}

fn main() {
    let mut list = Vec::new();
    let mut name = String::from("rust");

    println!("{}", is_long(&name));
    add_mark(&mut name);
    println!("{name}");

    // name 은 여기서 list 안으로 옮겨 간다
    keep(&mut list, name);
    println!("{list:?}");
}
