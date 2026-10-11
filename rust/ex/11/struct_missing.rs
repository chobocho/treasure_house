struct Excerpt {
    part: &str,
}

fn main() {
    let e = Excerpt { part: "hello" };
    println!("{}", e.part);
}
//@ expect: E0106
