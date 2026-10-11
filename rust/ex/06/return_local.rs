fn shout(s: &String) -> &String {
    let loud = s.to_uppercase();
    &loud
}

fn main() {
    let s = String::from("hello");
    println!("{}", shout(&s));
}
//@ expect: E0515
