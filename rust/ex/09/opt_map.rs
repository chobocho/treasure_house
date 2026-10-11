fn main() {
    let name: Option<&str> = Some("ferris");
    let nobody: Option<&str> = None;

    // map: 안에 값이 있으면 바꾸고, 없으면 None 그대로.
    println!("{:?}", name.map(|s| s.len()));
    println!("{:?}", nobody.map(|s| s.len()));
    println!("{:?}", name.map(|s| s.to_uppercase()));
}
