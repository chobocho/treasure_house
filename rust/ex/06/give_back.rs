// 받은 String 을 결과와 함께 돌려준다
fn measure(s: String) -> (String, usize) {
    let n = s.len();
    (s, n)
}

fn main() {
    let s = String::from("hello");
    let (s, n) = measure(s);
    println!("{s} 는 {n}글자");
}
