// 받은 클로저를 그대로 돌려준다. 하는 일은 조건을 거는 것뿐이다.
fn constrain<F>(f: F) -> F
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    f
}

fn show(words: &[&str], pick: impl Fn(&str) -> &str) {
    for w in words {
        println!("{}", pick(w));
    }
}

fn main() {
    // 조건이 걸린 자리에 바로 적는다.
    show(&["hello world"], |s| s.split(' ').next().unwrap_or(""));
    // 변수에 담아야 하면 constrain 을 거친다.
    let first = constrain(|s| s.split(' ').next().unwrap_or(""));
    println!("{}", first("hello world"));
    show(&["ab cd", "ef"], first);
}
