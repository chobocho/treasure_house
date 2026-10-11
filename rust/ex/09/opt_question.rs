fn initials(full: &str) -> Option<String> {
    let mut words = full.split(' ');
    // ? — None 이면 바로 None 을 돌려주고, Some 이면 속을 꺼낸다.
    let a = words.next()?.chars().next()?;
    let b = words.next()?.chars().next()?;
    Some(format!("{a}{b}"))
}

fn main() {
    println!("{:?}", initials("Graydon Hoare"));
    println!("{:?}", initials("Ferris"));
}
