fn check(name: &str, value: bool) -> bool {
    println!("  {name} 평가");
    value
}

fn main() {
    // && 와 || 는 필요한 만큼만 평가한다(단락 평가).
    println!("{}", check("a", false) && check("b", true));
    println!("{}", check("c", true) || check("d", false));
    println!("{}", !true);
}
