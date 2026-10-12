use std::any::Any;

// 상자째 받아서, String 이 들었으면 꺼내 가진다.
fn take_string(b: Box<dyn Any>) -> Result<String, Box<dyn Any>> {
    b.downcast::<String>().map(|s| *s)
}

fn main() {
    let boxes: Vec<Box<dyn Any>> =
        vec![Box::new(String::from("hi")), Box::new(7_u8)];
    for b in boxes {
        match take_string(b) {
            Ok(s) => println!("꺼냈다: {s}"),
            // 실패하면 상자가 그대로 돌아온다.
            Err(b) => {
                println!("String 이 아니다. u8 인가: {}", b.is::<u8>())
            }
        }
    }

    let b: Box<dyn Any> = Box::new(7_u8);
    // &b 는 상자를, as_ref() 는 상자 속을 가리킨다.
    let outer: &dyn Any = &b;
    let inner: &dyn Any = b.as_ref();
    println!("{} {}", outer.is::<u8>(), inner.is::<u8>());
    println!("{}", outer.is::<Box<dyn Any>>());
}
