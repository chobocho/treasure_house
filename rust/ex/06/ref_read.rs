// &String: 빌려서 읽기만 한다. 주인은 바뀌지 않는다.
fn length(s: &String) -> usize {
    s.len()
}

fn main() {
    let s = String::from("hello");
    // &s 는 s 를 가리키는 참조를 만든다
    let n = length(&s);

    // 넘긴 뒤에도 s 는 main 의 것이다
    println!("{s} 는 {n}글자");
    println!("다시 불러도 {}글자", length(&s));
}
