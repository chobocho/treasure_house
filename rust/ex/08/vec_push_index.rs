fn main() {
    let mut names = vec![String::from("kim"), String::from("lee")];
    // 참조 대신 그 자리의 인덱스를 적어 둔다
    let last = names.len() - 1;
    names.push(String::from("park"));
    println!("{} {names:?}", names[last]);
}
