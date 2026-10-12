enum Event {
    Click { x: i32, y: i32 },
    Key(char),
    // 나중에 더한 이벤트
    Scroll,
}

fn handle(event: &Event) -> String {
    match event {
        Event::Click { x, y } => format!("클릭 ({x}, {y})"),
        Event::Key(c) => format!("키 {c}"),
    }
}

fn main() {
    let events = vec![
        Event::Click { x: 3, y: 4 },
        Event::Key('q'),
        Event::Scroll,
    ];
    for e in &events {
        println!("{}", handle(e));
    }
}
//@ expect: E0004
