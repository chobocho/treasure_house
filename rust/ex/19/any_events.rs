use std::any::Any;

struct Click {
    x: i32,
    y: i32,
}
struct Key(char);
// 나중에 더한 이벤트
struct Scroll;

fn handle(event: &dyn Any) -> String {
    if let Some(c) = event.downcast_ref::<Click>() {
        format!("클릭 ({}, {})", c.x, c.y)
    } else if let Some(k) = event.downcast_ref::<Key>() {
        format!("키 {}", k.0)
    } else {
        String::from("?")
    }
}

fn main() {
    let events: Vec<Box<dyn Any>> = vec![
        Box::new(Click { x: 3, y: 4 }),
        Box::new(Key('q')),
        Box::new(Scroll),
    ];
    for e in &events {
        println!("{}", handle(e.as_ref()));
    }
}
