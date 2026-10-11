// &mut String: 빌려서 고친다
fn add_world(s: &mut String) {
    s.push_str(", world");
}

fn main() {
    let mut s = String::from("hello");
    // 부르는 쪽도 &mut 라고 적는다
    add_world(&mut s);
    println!("{s}");
}
