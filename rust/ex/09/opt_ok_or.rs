fn find(names: &[&str], key: &str) -> Option<usize> {
    names.iter().position(|n| *n == key)
}

fn main() {
    let names = ["kim", "lee"];
    // Option → Result: 없을 때의 까닭을 붙인다.
    let a: Result<usize, String> =
        find(&names, "lee").ok_or(String::from("그런 이름이 없다"));
    let b: Result<usize, String> =
        find(&names, "park").ok_or(String::from("그런 이름이 없다"));
    println!("{a:?}\n{b:?}");
    // Result → Option: 까닭을 버린다.
    println!(
        "{:?} {:?}",
        "42".parse::<i32>().ok(),
        "x".parse::<i32>().ok()
    );
}
