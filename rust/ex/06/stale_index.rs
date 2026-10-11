// 첫 낱말이 끝나는 자리(바이트 번호)를 돌려준다
fn first_word_end(s: &String) -> usize {
    let bytes = s.as_bytes();
    for i in 0..bytes.len() {
        if bytes[i] == b' ' {
            return i;
        }
    }
    s.len()
}

fn main() {
    let mut s = String::from("hello world");
    let end = first_word_end(&s);
    println!("end = {end}, len = {}", s.len());

    s.clear(); // 문자열을 비운다

    // end 는 여전히 5 다. 그 자리에 글자는 이제 없다.
    println!("end = {end}, len = {}", s.len());
}
