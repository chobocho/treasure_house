fn main() {
    let s = String::from("hello");
    let r = &s;
    let t = s;
    println!("{r} {t}");
}
//@ expect: E0505
