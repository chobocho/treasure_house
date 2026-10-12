use std::ptr;

// at 은 같은 값의 text 를 가리키게 할 포인터다.
struct Tagged {
    text: String,
    at: *const String,
}

impl Tagged {
    // at 이 지금의 text 를 가리키는가. 주소만 견주고 따라가지 않는다.
    fn points_to_self(&self) -> bool {
        ptr::eq(self.at, &self.text)
    }
}

fn main() {
    let mut tag = Tagged {
        text: String::from("ferris"),
        at: ptr::null(),
    };
    tag.at = &raw const tag.text;
    println!("만든 자리에서: {}", tag.points_to_self());

    // 값을 힙으로 옮긴다. at 에 든 주소는 고쳐지지 않고 따라간다.
    let boxed = Box::new(tag);
    println!("상자로 옮긴 뒤: {}", boxed.points_to_self());
    println!("text 는 그대로: {}", boxed.text);
}
