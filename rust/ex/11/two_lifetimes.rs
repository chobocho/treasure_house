// 두 참조의 수명이 서로 상관없을 때는 이름을 둘 쓴다.
fn describe<'a, 'b>(name: &'a str, note: &'b str) -> &'a str {
    println!("{name}: {note}");
    name
}

fn main() {
    let name = String::from("ferris");
    let who;
    {
        let note = String::from("게");
        who = describe(&name, &note);
    }
    println!("{who}");
}
