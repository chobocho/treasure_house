fn main() {
    let mut names = vec![String::from("kim"), String::from("lee")];
    // 지금의 마지막 이름을 빌려 둔다
    let last = &names[names.len() - 1];
    names.push(String::from("park"));
    println!("{last} {names:?}");
}
//@ expect: E0502
