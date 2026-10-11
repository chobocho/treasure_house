fn takes_owned(s: String) -> usize {
    s.len()
}

fn takes_borrowed(s: &str) -> usize {
    s.len()
}

fn main() {
    let lit = "글자";
    let owned = lit.to_string();

    println!("{}", takes_owned(owned.clone())); // 복제해 넘긴다
    println!("{}", takes_borrowed(&owned)); // &String → &str
    println!("{}", takes_borrowed(owned.as_str())); // 메서드로도 된다
    println!("{}", takes_borrowed(lit));
    println!("{}", takes_borrowed(&owned[..3])); // 일부만
    println!("{}", takes_owned(owned)); // 마지막에는 넘겨줘도 된다
}
