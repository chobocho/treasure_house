use std::mem;
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

// 값을 상자에 먼저 담고, 그 자리의 text 를 at 에 적는다.
fn boxed(text: &str) -> Box<Tagged> {
    let mut tag = Box::new(Tagged {
        text: String::from(text),
        at: ptr::null(),
    });
    tag.at = &raw const tag.text;
    tag
}

fn main() {
    // 상자를 옮긴다: 함수 밖으로, 다른 변수로, 벡터 안으로.
    let a = boxed("ferris");
    println!("함수가 돌려준 상자: {}", a.points_to_self());
    let moved = a;
    println!("다른 변수로 옮긴 상자: {}", moved.points_to_self());
    let mut shelf = vec![moved];
    println!("벡터에 넣은 상자: {}", shelf[0].points_to_self());

    // 상자 속의 값끼리 맞바꾼다. 이번에는 값이 자리를 옮긴다.
    let mut b = boxed("corro");
    mem::swap(&mut *shelf[0], &mut *b);
    let (first, second) = (&shelf[0], &b);
    println!("{}: {}", first.text, first.points_to_self());
    println!("{}: {}", second.text, second.points_to_self());
}
