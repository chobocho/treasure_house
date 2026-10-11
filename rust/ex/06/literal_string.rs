use std::any::type_name_of_val;

fn main() {
    // 리터럴은 실행 파일 안에 박혀 있다. 고칠 수 없다.
    let lit = "hello";

    // String 은 글자를 힙에 둔다. 그래서 늘릴 수 있다.
    let mut s = String::from("hello");
    s.push_str(", world");

    println!("{:<13} {}", lit, type_name_of_val(&lit));
    println!("{:<13} {}", s, type_name_of_val(&s));
}
