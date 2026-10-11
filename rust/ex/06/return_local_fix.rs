// 새로 만든 값은 참조가 아니라 값으로 돌려준다
fn shout(s: &String) -> String {
    s.to_uppercase()
}

fn main() {
    let s = String::from("hello");
    let loud = shout(&s);
    println!("{s} {loud}");
}
