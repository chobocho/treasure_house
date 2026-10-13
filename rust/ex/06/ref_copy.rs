fn main() {
    let s = String::from("hello");
    let r = &s;
    // 불변 참조를 대입하면 참조가 복사된다
    let r2 = r;
    println!("{r} {r2}");

    // 문자열 리터럴의 타입 &str 도 불변 참조다
    let word = "rust";
    let again = word;
    println!("{word} {again}");
}
