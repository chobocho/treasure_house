struct Excerpt<'a> {
    part: &'a str,
}

fn main() {
    let e;
    {
        let novel = String::from("옛날 옛적에.");
        e = Excerpt { part: &novel };
    } // novel 이 사라진다
    println!("{}", e.part);
}
//@ expect: E0597
