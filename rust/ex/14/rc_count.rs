use std::rc::Rc;

fn main() {
    let a = Rc::new(String::from("함께 쓰는 값"));
    println!("만든 뒤: {}", Rc::strong_count(&a));
    let b = Rc::clone(&a);
    println!("b 를 만든 뒤: {}", Rc::strong_count(&a));
    {
        let _c = Rc::clone(&a);
        println!("블록 안: {}", Rc::strong_count(&a));
    }
    println!("블록 뒤: {}", Rc::strong_count(&a));
    drop(b);
    println!("b 를 버린 뒤: {}", Rc::strong_count(&a));
    // a.clone() 이라고 써도 같다 — 같은 값을 가리킨다.
    println!("{}", Rc::ptr_eq(&a, &a.clone()));
}
