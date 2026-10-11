// 돌려주는 것은 늘 a 쪽이다 — b 에는 'a 를 붙이지 않는다.
fn first<'a>(a: &'a str, b: &str) -> &'a str {
    println!("(b 는 {} 글자)", b.len());
    a
}

fn main() {
    let x = String::from("apple");
    let kept;
    {
        let y = String::from("fig");
        kept = first(&x, &y);
    } // y 가 사라져도 된다 — 결과는 x 에만 매여 있다
    println!("{kept}");
}
