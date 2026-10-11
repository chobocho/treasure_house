// 받은 것의 일부를 가리킨다 → 빌린 것을 돌려준다
fn head3(s: &str) -> &str {
    &s[..3]
}

// 새로 만든다 → 값을 돌려준다
fn with_mark(s: &str) -> String {
    let mut out = String::from(s);
    out.push('!');
    out
}

fn main() {
    let s = String::from("hello");
    let head = head3(&s);
    let loud = with_mark(&s);
    println!("{head} {loud}");

    // s 를 옮긴다. head 는 s 를 빌린 것이라 여기까지다.
    let t = s;
    // loud 는 따로 선 값이라 s 가 없어도 쓴다
    println!("{t} {loud}");
}
