use std::rc::Rc;

// 계산대. 가게의 계산대들이 장부 하나를 함께 쓴다.
struct Till {
    name: String,
    book: Rc<Vec<String>>,
}

impl Till {
    fn sell(&self, item: &str, won: u32) {
        let line = format!("{} {item} {won}", self.name);
        self.book.push(line);
    }
}

fn main() {
    let book = Rc::new(Vec::new());
    let front = Till {
        name: String::from("앞"),
        book: Rc::clone(&book),
    };
    let back = Till {
        name: String::from("뒤"),
        book: Rc::clone(&book),
    };
    front.sell("연필", 450);
    back.sell("공책", 1200);
    front.sell("지우개", 80);

    for line in book.iter() {
        println!("{line}");
    }
    let count = book.len();
    println!("{count}줄, 주인 {}명", Rc::strong_count(&book));
}
//@ expect: E0596
